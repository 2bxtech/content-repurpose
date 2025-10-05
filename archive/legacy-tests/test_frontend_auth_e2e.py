"""
End-to-End Frontend Authentication Test
Simulates complete frontend auth workflow using the same endpoints and logic
"""

import httpx
import time
from typing import Dict, Any


class FrontendAuthTester:
    """Simulates frontend authentication workflow"""
    
    def __init__(self):
        self.base_url = "http://localhost:8000/api"
        self.client = httpx.Client(timeout=10.0)
        self.token = None
        self.user_data = None
        
    def setup_headers(self, include_auth=True) -> Dict[str, str]:
        """Setup headers like frontend axios does"""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Origin": "http://localhost:3000",  # Simulate frontend origin
            "User-Agent": "Frontend-Auth-Test/1.0"
        }
        
        if include_auth and self.token:
            headers["Authorization"] = f"Bearer {self.token}"
            
        return headers
        
    def test_cors_preflight(self) -> Dict[str, Any]:
        """Test CORS preflight like browser does"""
        print("🔍 Testing CORS preflight (OPTIONS request)...")
        
        try:
            response = self.client.options(
                f"{self.base_url}/auth/register",
                headers={
                    "Origin": "http://localhost:3000",
                    "Access-Control-Request-Method": "POST",
                    "Access-Control-Request-Headers": "Content-Type"
                }
            )
            
            cors_headers = {
                "access-control-allow-origin": response.headers.get("access-control-allow-origin"),
                "access-control-allow-credentials": response.headers.get("access-control-allow-credentials"),
                "access-control-allow-methods": response.headers.get("access-control-allow-methods"),
            }
            
            success = response.status_code == 200
            return {
                "success": success,
                "status": response.status_code,
                "cors_headers": cors_headers,
                "message": "CORS preflight successful" if success else f"CORS failed: {response.status_code}"
            }
            
        except Exception as e:
            return {
                "success": False,
                "status": "error", 
                "message": f"CORS preflight failed: {e}"
            }
    
    def test_register(self, username: str, email: str, password: str) -> Dict[str, Any]:
        """Test user registration exactly like frontend does"""
        print(f"📝 Testing user registration for: {email}")
        
        user_data = {
            "username": username,
            "email": email,
            "password": password
        }
        
        try:
            response = self.client.post(
                f"{self.base_url}/auth/register",
                json=user_data,
                headers=self.setup_headers(include_auth=False)
            )
            
            success = response.status_code in [200, 201]
            
            result = {
                "success": success,
                "status": response.status_code,
                "headers": dict(response.headers),
            }
            
            if success:
                try:
                    result["data"] = response.json()
                    result["message"] = "Registration successful"
                except:
                    result["message"] = "Registration successful (no JSON response)"
            else:
                try:
                    error_data = response.json()
                    if isinstance(error_data.get("detail"), list):
                        result["message"] = error_data["detail"][0].get("msg", str(error_data["detail"]))
                    else:
                        result["message"] = str(error_data.get("detail", f"Registration failed: {response.status_code}"))
                except:
                    result["message"] = f"Registration failed: {response.status_code} - {response.text}"
                    
            return result
            
        except Exception as e:
            return {
                "success": False,
                "status": "error",
                "message": f"Registration request failed: {e}"
            }
    
    def test_login(self, email: str, password: str) -> Dict[str, Any]:
        """Test login exactly like frontend does (OAuth2 FormData)"""
        print(f"🔑 Testing login for: {email}")
        
        try:
            # Frontend uses FormData for OAuth2 token endpoint
            form_data = f"username={email}&password={password}"
            
            response = self.client.post(
                f"{self.base_url}/auth/token",
                content=form_data,
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Accept": "application/json",
                    "Origin": "http://localhost:3000"
                }
            )
            
            success = response.status_code == 200
            
            result = {
                "success": success,
                "status": response.status_code,
                "headers": dict(response.headers),
            }
            
            if success:
                try:
                    token_data = response.json()
                    self.token = token_data.get("access_token")
                    result["data"] = token_data
                    result["message"] = "Login successful"
                    result["token_received"] = bool(self.token)
                except:
                    result["message"] = "Login successful but no token received"
            else:
                try:
                    error_data = response.json()
                    if isinstance(error_data.get("detail"), list):
                        result["message"] = error_data["detail"][0].get("msg", str(error_data["detail"]))
                    else:
                        result["message"] = str(error_data.get("detail", f"Login failed: {response.status_code}"))
                except:
                    result["message"] = f"Login failed: {response.status_code} - {response.text}"
                    
            return result
            
        except Exception as e:
            return {
                "success": False,
                "status": "error",
                "message": f"Login request failed: {e}"
            }
    
    def test_get_current_user(self) -> Dict[str, Any]:
        """Test getting current user like frontend does"""
        print("👤 Testing get current user...")
        
        if not self.token:
            return {
                "success": False,
                "message": "No token available for authentication"
            }
        
        try:
            response = self.client.get(
                f"{self.base_url}/auth/me",
                headers=self.setup_headers(include_auth=True)
            )
            
            success = response.status_code == 200
            
            result = {
                "success": success,
                "status": response.status_code,
                "headers": dict(response.headers),
            }
            
            if success:
                try:
                    self.user_data = response.json()
                    result["data"] = self.user_data
                    result["message"] = "User data retrieved successfully"
                except:
                    result["message"] = "User endpoint successful but no data"
            else:
                try:
                    error_data = response.json()
                    result["message"] = str(error_data.get("detail", f"Get user failed: {response.status_code}"))
                except:
                    result["message"] = f"Get user failed: {response.status_code} - {response.text}"
                    
            return result
            
        except Exception as e:
            return {
                "success": False,
                "status": "error",
                "message": f"Get user request failed: {e}"
            }
    
    def test_protected_endpoint(self) -> Dict[str, Any]:
        """Test accessing protected transformations endpoint"""
        print("🔒 Testing protected transformations endpoint...")
        
        if not self.token:
            return {
                "success": False,
                "message": "No token available for protected endpoint test"
            }
        
        transformation_data = {
            "sourceDocument": "Test document content for authentication test",
            "transformationType": "summary",
            "parameters": {
                "wordCount": 50,
                "tone": "professional"
            }
        }
        
        try:
            response = self.client.post(
                f"{self.base_url}/transformations",
                json=transformation_data,
                headers=self.setup_headers(include_auth=True)
            )
            
            success = response.status_code in [200, 201]
            
            result = {
                "success": success,
                "status": response.status_code,
                "headers": dict(response.headers),
            }
            
            if success:
                try:
                    result["data"] = response.json()
                    result["message"] = "Protected endpoint accessed successfully"
                except:
                    result["message"] = "Protected endpoint successful"
            else:
                try:
                    error_data = response.json()
                    result["message"] = str(error_data.get("detail", f"Protected endpoint failed: {response.status_code}"))
                except:
                    result["message"] = f"Protected endpoint failed: {response.status_code} - {response.text}"
                    
            return result
            
        except Exception as e:
            return {
                "success": False,
                "status": "error",
                "message": f"Protected endpoint request failed: {e}"
            }
    
    def run_complete_workflow(self) -> Dict[str, Any]:
        """Run complete frontend authentication workflow"""
        print("🚀 Starting Complete Frontend Authentication Workflow Test")
        print("=" * 70)
        
        # Generate unique test user
        timestamp = int(time.time())
        test_user = {
            "username": f"testuser_{timestamp}",
            "email": f"test_{timestamp}@example.com",
            "password": "StrongTestPassword123!@#"
        }
        
        results = {}
        
        # Step 1: CORS Preflight
        results["cors_preflight"] = self.test_cors_preflight()
        
        # Step 2: User Registration
        results["registration"] = self.test_register(
            test_user["username"], 
            test_user["email"], 
            test_user["password"]
        )
        
        # Step 3: User Login
        if results["registration"]["success"]:
            results["login"] = self.test_login(test_user["email"], test_user["password"])
        else:
            # Try login anyway to test the endpoint
            results["login"] = self.test_login(test_user["email"], test_user["password"])
        
        # Step 4: Get Current User
        if results["login"]["success"]:
            results["get_user"] = self.test_get_current_user()
        else:
            results["get_user"] = {"success": False, "message": "Skipped - no valid token"}
        
        # Step 5: Protected Endpoint
        if results["login"]["success"]:
            results["protected_endpoint"] = self.test_protected_endpoint()
        else:
            results["protected_endpoint"] = {"success": False, "message": "Skipped - no valid token"}
        
        return {
            "test_user": test_user,
            "results": results,
            "overall_success": self.calculate_overall_success(results)
        }
    
    def calculate_overall_success(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate overall test success"""
        total_tests = len(results)
        successful_tests = sum(1 for result in results.values() if result.get("success", False))
        
        critical_tests = ["cors_preflight", "registration", "login"]
        critical_success = all(results.get(test, {}).get("success", False) for test in critical_tests)
        
        return {
            "total_tests": total_tests,
            "successful_tests": successful_tests,
            "success_rate": successful_tests / total_tests * 100,
            "critical_tests_passed": critical_success,
            "ready_for_frontend": critical_success and successful_tests >= 4
        }
    
    def print_results(self, workflow_result: Dict[str, Any]):
        """Print detailed test results"""
        test_user = workflow_result["test_user"]
        results = workflow_result["results"] 
        overall = workflow_result["overall_success"]
        
        print("\n" + "=" * 70)
        print("📊 FRONTEND AUTHENTICATION WORKFLOW RESULTS")
        print("=" * 70)
        
        print(f"Test User: {test_user['email']}")
        print(f"Password: {test_user['password']}")
        print()
        
        # Individual test results
        test_names = {
            "cors_preflight": "🔍 CORS Preflight",
            "registration": "📝 User Registration", 
            "login": "🔑 User Login",
            "get_user": "👤 Get Current User",
            "protected_endpoint": "🔒 Protected Endpoint"
        }
        
        for test_key, test_name in test_names.items():
            result = results.get(test_key, {})
            status = "✅ PASS" if result.get("success") else "❌ FAIL"
            message = result.get("message", "No result")
            print(f"{status} {test_name}: {message}")
        
        print("\n" + "-" * 70)
        print("📈 OVERALL RESULTS")
        print("-" * 70)
        print(f"Tests Passed: {overall['successful_tests']}/{overall['total_tests']}")
        print(f"Success Rate: {overall['success_rate']:.1f}%")
        print(f"Critical Tests (CORS, Registration, Login): {'✅ PASS' if overall['critical_tests_passed'] else '❌ FAIL'}")
        
        if overall["ready_for_frontend"]:
            print("\n🎉 FRONTEND READY!")
            print("✅ All critical authentication flows are working")
            print("✅ Frontend should work correctly with this backend")
            print("✅ CORS is properly configured")
            print("✅ Registration and login endpoints functional")
        else:
            print("\n⚠️ FRONTEND NOT READY")
            print("❌ Critical authentication issues found")
            print("❌ Frontend may experience authentication problems")
            
        return overall["ready_for_frontend"]


def main():
    """Run the complete frontend authentication test"""
    print("🧪 Frontend Authentication End-to-End Test")
    print("Testing the complete workflow that the frontend React app uses")
    print()
    
    tester = FrontendAuthTester()
    
    try:
        workflow_result = tester.run_complete_workflow()
        frontend_ready = tester.print_results(workflow_result)
        
        if frontend_ready:
            print("\n🚀 NEXT STEPS:")
            print("1. Start your React frontend: npm start")
            print("2. Navigate to the registration page")
            print("3. Try registering with a strong password (12+ chars)")
            print("4. Test login with the registered credentials")
            print("5. Verify you can access the dashboard")
            
        return frontend_ready
        
    except Exception as e:
        print(f"\n❌ TEST FRAMEWORK ERROR: {e}")
        return False
    finally:
        tester.client.close()


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)