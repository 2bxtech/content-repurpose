#!/bin/bash
# Database Migration and Management Script
# Handles database operations for different environments

set -e  # Exit on any error

# Default configuration
ENVIRONMENT=${ENVIRONMENT:-development}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Load environment configuration
load_environment() {
    local env_file="$PROJECT_ROOT/deployments/.env.$ENVIRONMENT"
    
    if [[ -f "$env_file" ]]; then
        log_info "Loading environment configuration for: $ENVIRONMENT"
        set -a  # Automatically export variables
        source "$env_file"
        set +a
    else
        log_warning "Environment file not found: $env_file"
        log_info "Using default/system environment variables"
    fi
}

# Check database connectivity
check_database() {
    log_info "Checking database connectivity for $ENVIRONMENT environment..."
    
    local max_attempts=30
    local attempt=1
    
    while [[ $attempt -le $max_attempts ]]; do
        if pg_isready -h "${DATABASE_HOST:-localhost}" -p "${DATABASE_PORT:-5432}" -U "${DATABASE_USER:-postgres}" -d "${DATABASE_NAME:-content_repurpose}" > /dev/null 2>&1; then
            log_success "Database is ready"
            return 0
        fi
        
        log_info "Attempt $attempt/$max_attempts - Database not ready, waiting 2 seconds..."
        sleep 2
        ((attempt++))
    done
    
    log_error "Database connection failed after $max_attempts attempts"
    return 1
}

# Wait for services (Docker Compose)
wait_for_services() {
    log_info "Waiting for services to be ready..."
    
    # Wait for database
    check_database
    
    # Wait for Redis if configured
    if [[ -n "${REDIS_HOST}" ]]; then
        log_info "Checking Redis connectivity..."
        local max_attempts=30
        local attempt=1
        
        while [[ $attempt -le $max_attempts ]]; do
            if redis-cli -h "${REDIS_HOST}" -p "${REDIS_PORT:-6379}" ping > /dev/null 2>&1; then
                log_success "Redis is ready"
                break
            fi
            
            log_info "Attempt $attempt/$max_attempts - Redis not ready, waiting 1 second..."
            sleep 1
            ((attempt++))
        done
        
        if [[ $attempt -gt $max_attempts ]]; then
            log_warning "Redis connection failed, continuing anyway..."
        fi
    fi
}

# Run database migrations
run_migrations() {
    log_info "Running database migrations for $ENVIRONMENT environment..."
    
    cd "$BACKEND_DIR"
    
    # Check if alembic is available
    if ! command -v alembic &> /dev/null; then
        log_error "Alembic not found. Please install requirements first."
        return 1
    fi
    
    # Run migrations
    if alembic upgrade head; then
        log_success "Database migrations completed successfully"
    else
        log_error "Database migration failed"
        return 1
    fi
}

# Create new migration
create_migration() {
    local message="$1"
    
    if [[ -z "$message" ]]; then
        log_error "Migration message is required"
        echo "Usage: $0 create-migration \"Migration description\""
        return 1
    fi
    
    log_info "Creating new migration: $message"
    
    cd "$BACKEND_DIR"
    
    if alembic revision --autogenerate -m "$message"; then
        log_success "Migration created successfully"
        log_info "Please review the generated migration file before applying"
    else
        log_error "Migration creation failed"
        return 1
    fi
}

# Check migration status
check_migration_status() {
    log_info "Checking migration status for $ENVIRONMENT environment..."
    
    cd "$BACKEND_DIR"
    
    log_info "Current migration status:"
    alembic current
    
    log_info "Available migrations:"
    alembic history
}

# Initialize database (fresh setup)
init_database() {
    log_info "Initializing database for $ENVIRONMENT environment..."
    
    cd "$BACKEND_DIR"
    
    # Check if database exists and has tables
    local table_count
    table_count=$(psql "${DATABASE_URL_SYNC}" -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" 2>/dev/null | xargs || echo "0")
    
    if [[ "$table_count" -gt 0 ]]; then
        log_warning "Database already contains $table_count tables"
        read -p "Do you want to continue and run migrations? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "Database initialization cancelled"
            return 0
        fi
    fi
    
    # Run migrations
    run_migrations
    
    log_success "Database initialization completed"
}

# Backup database
backup_database() {
    local backup_dir="$PROJECT_ROOT/backups"
    local timestamp=$(date +"%Y%m%d_%H%M%S")
    local backup_file="$backup_dir/${ENVIRONMENT}_database_backup_$timestamp.sql"
    
    log_info "Creating database backup for $ENVIRONMENT environment..."
    
    # Create backup directory if it doesn't exist
    mkdir -p "$backup_dir"
    
    # Create backup
    if pg_dump "${DATABASE_URL_SYNC}" > "$backup_file"; then
        log_success "Database backup created: $backup_file"
        
        # Compress backup
        if command -v gzip &> /dev/null; then
            gzip "$backup_file"
            log_success "Backup compressed: $backup_file.gz"
        fi
    else
        log_error "Database backup failed"
        return 1
    fi
}

# Restore database from backup
restore_database() {
    local backup_file="$1"
    
    if [[ -z "$backup_file" ]]; then
        log_error "Backup file path is required"
        echo "Usage: $0 restore-database /path/to/backup.sql"
        return 1
    fi
    
    if [[ ! -f "$backup_file" ]]; then
        log_error "Backup file not found: $backup_file"
        return 1
    fi
    
    log_warning "This will overwrite the current database for $ENVIRONMENT environment"
    read -p "Are you sure you want to continue? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Database restore cancelled"
        return 0
    fi
    
    log_info "Restoring database from: $backup_file"
    
    # Handle compressed files
    if [[ "$backup_file" == *.gz ]]; then
        if zcat "$backup_file" | psql "${DATABASE_URL_SYNC}"; then
            log_success "Database restored successfully"
        else
            log_error "Database restore failed"
            return 1
        fi
    else
        if psql "${DATABASE_URL_SYNC}" < "$backup_file"; then
            log_success "Database restored successfully"
        else
            log_error "Database restore failed"
            return 1
        fi
    fi
}

# Reset database (drop and recreate)
reset_database() {
    log_warning "This will completely reset the database for $ENVIRONMENT environment"
    read -p "Are you sure you want to continue? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Database reset cancelled"
        return 0
    fi
    
    log_info "Resetting database..."
    
    cd "$BACKEND_DIR"
    
    # Drop all tables
    if alembic downgrade base; then
        log_success "Database tables dropped"
    else
        log_warning "Failed to drop tables via Alembic, continuing..."
    fi
    
    # Run fresh migrations
    run_migrations
    
    log_success "Database reset completed"
}

# Show help
show_help() {
    echo "Database Migration and Management Script"
    echo ""
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  migrate                     Run database migrations"
    echo "  create-migration MESSAGE    Create a new migration"
    echo "  status                      Check migration status"
    echo "  init                        Initialize database (fresh setup)"
    echo "  backup                      Create database backup"
    echo "  restore-database FILE       Restore database from backup"
    echo "  reset                       Reset database (drop and recreate)"
    echo "  wait-services              Wait for services to be ready"
    echo "  check-db                   Check database connectivity"
    echo "  help                       Show this help message"
    echo ""
    echo "Environment Variables:"
    echo "  ENVIRONMENT=development    Set environment (development, staging, production)"
    echo ""
    echo "Examples:"
    echo "  $0 migrate"
    echo "  $0 create-migration \"Add user preferences table\""
    echo "  ENVIRONMENT=staging $0 init"
    echo "  $0 backup"
    echo "  $0 restore-database /path/to/backup.sql"
}

# Main script logic
main() {
    local command="$1"
    shift || true
    
    # Load environment configuration
    load_environment
    
    case "$command" in
        "migrate")
            wait_for_services
            run_migrations
            ;;
        "create-migration")
            create_migration "$1"
            ;;
        "status")
            check_migration_status
            ;;
        "init")
            wait_for_services
            init_database
            ;;
        "backup")
            backup_database
            ;;
        "restore-database")
            restore_database "$1"
            ;;
        "reset")
            wait_for_services
            reset_database
            ;;
        "wait-services")
            wait_for_services
            ;;
        "check-db")
            check_database
            ;;
        "help"|"--help"|"-h"|"")
            show_help
            ;;
        *)
            log_error "Unknown command: $command"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"