#!/bin/bash
# Deployment Orchestration Script
# Handles deployment to different environments with proper setup and validation

set -e  # Exit on any error

# Default configuration
ENVIRONMENT=${ENVIRONMENT:-staging}
ACTION=${ACTION:-deploy}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
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

log_step() {
    echo -e "${PURPLE}[STEP]${NC} $1"
}

# Check if Docker and Docker Compose are available
check_docker() {
    log_info "Checking Docker installation..."
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed or not in PATH"
        return 1
    fi
    
    if ! docker info &> /dev/null; then
        log_error "Docker daemon is not running"
        return 1
    fi
    
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        log_error "Docker Compose is not installed or not in PATH"
        return 1
    fi
    
    log_success "Docker environment is ready"
}

# Get Docker Compose command (handle both docker-compose and docker compose)
get_compose_cmd() {
    if command -v docker-compose &> /dev/null; then
        echo "docker-compose"
    elif docker compose version &> /dev/null; then
        echo "docker compose"
    else
        log_error "Docker Compose not found"
        exit 1
    fi
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
        log_info "Please create $env_file from the template"
        
        local template_file="$PROJECT_ROOT/deployments/.env.$ENVIRONMENT.template"
        if [[ -f "$template_file" ]]; then
            log_info "Template available at: $template_file"
        fi
        return 1
    fi
}

# Validate environment configuration
validate_environment() {
    log_info "Validating environment configuration..."
    
    local required_vars=()
    local missing_vars=()
    
    # Define required variables based on environment
    if [[ "$ENVIRONMENT" == "production" ]]; then
        required_vars=(
            "DATABASE_PASSWORD"
            "REDIS_PASSWORD"
            "SECRET_KEY"
            "REFRESH_SECRET_KEY"
            "SENTRY_DSN"
        )
    else
        required_vars=(
            "DATABASE_PASSWORD"
            "SECRET_KEY"
            "REFRESH_SECRET_KEY"
        )
    fi
    
    # Check for missing variables
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var}" ]]; then
            missing_vars+=("$var")
        fi
    done
    
    if [[ ${#missing_vars[@]} -gt 0 ]]; then
        log_error "Missing required environment variables:"
        for var in "${missing_vars[@]}"; do
            echo "  - $var"
        done
        return 1
    fi
    
    # Validate secret key lengths
    if [[ ${#SECRET_KEY} -lt 32 ]]; then
        log_error "SECRET_KEY must be at least 32 characters long"
        return 1
    fi
    
    if [[ ${#REFRESH_SECRET_KEY} -lt 32 ]]; then
        log_error "REFRESH_SECRET_KEY must be at least 32 characters long"
        return 1
    fi
    
    log_success "Environment configuration is valid"
}

# Build Docker images
build_images() {
    log_step "Building Docker images for $ENVIRONMENT environment..."
    
    local compose_cmd=$(get_compose_cmd)
    local compose_file="$PROJECT_ROOT/deployments/docker-compose.$ENVIRONMENT.yml"
    
    if [[ ! -f "$compose_file" ]]; then
        log_error "Docker Compose file not found: $compose_file"
        return 1
    fi
    
    cd "$PROJECT_ROOT"
    
    # Build images with proper caching
    if $compose_cmd -f "$compose_file" build --parallel; then
        log_success "Docker images built successfully"
    else
        log_error "Docker image build failed"
        return 1
    fi
}

# Deploy services
deploy_services() {
    log_step "Deploying services for $ENVIRONMENT environment..."
    
    local compose_cmd=$(get_compose_cmd)
    local compose_file="$PROJECT_ROOT/deployments/docker-compose.$ENVIRONMENT.yml"
    
    cd "$PROJECT_ROOT"
    
    # Pull latest base images
    log_info "Pulling latest base images..."
    $compose_cmd -f "$compose_file" pull postgres redis
    
    # Deploy services with proper ordering
    log_info "Starting infrastructure services (database, cache)..."
    $compose_cmd -f "$compose_file" up -d postgres redis
    
    # Wait for infrastructure services
    log_info "Waiting for infrastructure services to be ready..."
    sleep 10
    
    # Run database migrations
    log_info "Running database migrations..."
    "$SCRIPT_DIR/db-migrate.sh" migrate
    
    # Deploy application services
    log_info "Starting application services..."
    $compose_cmd -f "$compose_file" up -d
    
    log_success "Services deployed successfully"
}

# Check service health
check_health() {
    log_step "Checking service health..."
    
    local compose_cmd=$(get_compose_cmd)
    local compose_file="$PROJECT_ROOT/deployments/docker-compose.$ENVIRONMENT.yml"
    
    cd "$PROJECT_ROOT"
    
    # Wait for services to be healthy
    local max_attempts=30
    local attempt=1
    
    while [[ $attempt -le $max_attempts ]]; do
        log_info "Health check attempt $attempt/$max_attempts..."
        
        # Check if all services are healthy
        local unhealthy_services
        unhealthy_services=$($compose_cmd -f "$compose_file" ps --filter "health=unhealthy" --format "table {{.Service}}" | tail -n +2)
        
        if [[ -z "$unhealthy_services" ]]; then
            log_success "All services are healthy"
            return 0
        fi
        
        log_info "Unhealthy services: $unhealthy_services"
        sleep 10
        ((attempt++))
    done
    
    log_error "Some services failed health checks after $max_attempts attempts"
    
    # Show service status
    $compose_cmd -f "$compose_file" ps
    
    return 1
}

# Show service status
show_status() {
    local compose_cmd=$(get_compose_cmd)
    local compose_file="$PROJECT_ROOT/deployments/docker-compose.$ENVIRONMENT.yml"
    
    cd "$PROJECT_ROOT"
    
    log_info "Service status for $ENVIRONMENT environment:"
    $compose_cmd -f "$compose_file" ps
    
    echo ""
    log_info "Service logs (last 10 lines):"
    $compose_cmd -f "$compose_file" logs --tail=10
}

# Stop services
stop_services() {
    log_step "Stopping services for $ENVIRONMENT environment..."
    
    local compose_cmd=$(get_compose_cmd)
    local compose_file="$PROJECT_ROOT/deployments/docker-compose.$ENVIRONMENT.yml"
    
    cd "$PROJECT_ROOT"
    
    $compose_cmd -f "$compose_file" down
    
    log_success "Services stopped"
}

# Clean up resources
cleanup() {
    log_step "Cleaning up resources for $ENVIRONMENT environment..."
    
    local compose_cmd=$(get_compose_cmd)
    local compose_file="$PROJECT_ROOT/deployments/docker-compose.$ENVIRONMENT.yml"
    
    cd "$PROJECT_ROOT"
    
    # Stop and remove containers, networks
    $compose_cmd -f "$compose_file" down --remove-orphans
    
    # Optionally remove volumes (be careful in production!)
    if [[ "$ENVIRONMENT" != "production" ]]; then
        read -p "Remove volumes (all data will be lost)? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            $compose_cmd -f "$compose_file" down --volumes
            log_warning "Volumes removed - all data lost"
        fi
    fi
    
    # Clean up unused images
    docker image prune -f
    
    log_success "Cleanup completed"
}

# Update services (rolling update)
update_services() {
    log_step "Updating services for $ENVIRONMENT environment..."
    
    # Build new images
    build_images
    
    # Rolling update
    local compose_cmd=$(get_compose_cmd)
    local compose_file="$PROJECT_ROOT/deployments/docker-compose.$ENVIRONMENT.yml"
    
    cd "$PROJECT_ROOT"
    
    # Update services one by one to minimize downtime
    local services=("api" "celery-worker" "celery-beat")
    
    for service in "${services[@]}"; do
        log_info "Updating service: $service"
        $compose_cmd -f "$compose_file" up -d --no-deps "$service"
        
        # Wait a bit between updates
        sleep 5
    done
    
    # Check health after update
    check_health
    
    log_success "Services updated successfully"
}

# Generate deployment report
generate_report() {
    log_step "Generating deployment report..."
    
    local report_file="$PROJECT_ROOT/deployments/reports/deployment_$(date +%Y%m%d_%H%M%S).txt"
    mkdir -p "$(dirname "$report_file")"
    
    {
        echo "Deployment Report"
        echo "================"
        echo "Environment: $ENVIRONMENT"
        echo "Timestamp: $(date)"
        echo "User: $(whoami)"
        echo ""
        
        echo "Service Status:"
        echo "---------------"
        show_status
        
        echo ""
        echo "Environment Configuration:"
        echo "-------------------------"
        env | grep -E "(DATABASE|REDIS|API|CELERY)" | sort
        
    } > "$report_file"
    
    log_success "Deployment report generated: $report_file"
}

# Show logs
show_logs() {
    local service="$1"
    local compose_cmd=$(get_compose_cmd)
    local compose_file="$PROJECT_ROOT/deployments/docker-compose.$ENVIRONMENT.yml"
    
    cd "$PROJECT_ROOT"
    
    if [[ -n "$service" ]]; then
        log_info "Showing logs for service: $service"
        $compose_cmd -f "$compose_file" logs -f "$service"
    else
        log_info "Showing logs for all services"
        $compose_cmd -f "$compose_file" logs -f
    fi
}

# Show help
show_help() {
    echo "Deployment Orchestration Script"
    echo ""
    echo "Usage: $0 [ACTION] [OPTIONS]"
    echo ""
    echo "Actions:"
    echo "  deploy                      Full deployment (build + deploy + health check)"
    echo "  build                       Build Docker images only"
    echo "  start                       Start services"
    echo "  stop                        Stop services"
    echo "  restart                     Restart services"
    echo "  update                      Update services (rolling update)"
    echo "  status                      Show service status"
    echo "  health                      Check service health"
    echo "  logs [SERVICE]             Show logs (optionally for specific service)"
    echo "  cleanup                     Clean up resources"
    echo "  report                      Generate deployment report"
    echo "  help                        Show this help message"
    echo ""
    echo "Environment Variables:"
    echo "  ENVIRONMENT=staging         Set environment (development, staging, production)"
    echo ""
    echo "Examples:"
    echo "  $0 deploy"
    echo "  ENVIRONMENT=production $0 deploy"
    echo "  $0 logs api"
    echo "  $0 update"
    echo "  $0 status"
}

# Main script logic
main() {
    local action="$1"
    shift || true
    
    case "$action" in
        "deploy")
            check_docker
            load_environment
            validate_environment
            build_images
            deploy_services
            check_health
            generate_report
            log_success "Deployment completed successfully!"
            ;;
        "build")
            check_docker
            load_environment
            build_images
            ;;
        "start")
            check_docker
            load_environment
            deploy_services
            ;;
        "stop")
            check_docker
            load_environment
            stop_services
            ;;
        "restart")
            check_docker
            load_environment
            stop_services
            deploy_services
            check_health
            ;;
        "update")
            check_docker
            load_environment
            validate_environment
            update_services
            ;;
        "status")
            check_docker
            load_environment
            show_status
            ;;
        "health")
            check_docker
            load_environment
            check_health
            ;;
        "logs")
            check_docker
            load_environment
            show_logs "$1"
            ;;
        "cleanup")
            check_docker
            load_environment
            cleanup
            ;;
        "report")
            check_docker
            load_environment
            generate_report
            ;;
        "help"|"--help"|"-h"|"")
            show_help
            ;;
        *)
            log_error "Unknown action: $action"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"