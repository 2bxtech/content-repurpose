#!/usr/bin/env python3
"""
Quick manual test - just check if server is responding
"""

import subprocess
import sys
import time

def test_server_response():
    print("🔍 Quick Server Response Test")
    print("=" * 30)
    
    try:
        # Test basic connectivity
        result = subprocess.run([
            'curl', '-s', '-o', '/dev/null', '-w', '%{http_code}', 
            'http://localhost:8000'
        ], capture_output=True, text=True, timeout=5)
        
        if result.returncode == 0 and result.stdout == '200':
            print("✅ Server responding on port 8000")
        else:
            print(f"❌ Server response: {result.stdout}")
            return False
            
        # Test health endpoint
        result = subprocess.run([
            'curl', '-s', '-o', '/dev/null', '-w', '%{http_code}', 
            'http://localhost:8000/api/health'
        ], capture_output=True, text=True, timeout=5)
        
        if result.returncode == 0 and result.stdout == '200':
            print("✅ Health endpoint responding")
        else:
            print(f"❌ Health endpoint: {result.stdout}")
            
        # Test auth endpoint structure
        result = subprocess.run([
            'curl', '-s', '-o', '/dev/null', '-w', '%{http_code}', 
            'http://localhost:8000/docs'
        ], capture_output=True, text=True, timeout=5)
        
        if result.returncode == 0 and result.stdout == '200':
            print("✅ API documentation accessible")
        else:
            print(f"❌ API docs: {result.stdout}")
            
        print("\n🎯 BASIC CONNECTIVITY CONFIRMED")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    test_server_response()