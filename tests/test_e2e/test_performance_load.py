"""
End-to-end performance and load tests.

These tests validate application performance under various load conditions,
response times, memory usage, and concurrent user scenarios.
"""

import pytest
import time
import threading
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.config.database import get_db


class TestE2EPerformance:
    """End-to-end performance tests."""
    
    def test_api_response_time_benchmarks(self, db_session: Session):
        """Test API response time benchmarks for key endpoints."""
        def override_get_db():
            try:
                yield db_session
            finally:
                pass
        
        app.dependency_overrides[get_db] = override_get_db
        
        # Temporarily disable TrustedHostMiddleware
        original_middleware = app.user_middleware
        app.user_middleware = [m for m in app.user_middleware if 'TrustedHostMiddleware' not in str(type(m.cls))]
        
        try:
            with TestClient(app) as client:
                # Benchmark registration endpoint
                registration_times = []
                for i in range(5):
                    user_data = {"username": f"benchmark_user_{i}", "password": f"benchmark_pass_{i}123"}
                    
                    start_time = time.time()
                    response = client.post("/api/auth/register", json=user_data)
                    end_time = time.time()
                    
                    assert response.status_code == 201
                    registration_times.append(end_time - start_time)
                
                # Benchmark login endpoint
                login_times = []
                for i in range(5):
                    user_data = {"username": f"benchmark_user_{i}", "password": f"benchmark_pass_{i}123"}
                    
                    start_time = time.time()
                    response = client.post("/api/auth/login", json=user_data)
                    end_time = time.time()
                    
                    assert response.status_code == 200
                    login_times.append(end_time - start_time)
                
                # Benchmark protected endpoint
                token = client.post("/api/auth/login", json={"username": "benchmark_user_0", "password": "benchmark_pass_0123"}).json()["access_token"]
                headers = {"Authorization": f"Bearer {token}"}
                
                protected_times = []
                for _ in range(10):
                    start_time = time.time()
                    response = client.get("/api/user/protected", headers=headers)
                    end_time = time.time()
                    
                    assert response.status_code == 200
                    protected_times.append(end_time - start_time)
                
                # Performance assertions (adjust thresholds as needed)
                avg_registration_time = statistics.mean(registration_times)
                avg_login_time = statistics.mean(login_times)
                avg_protected_time = statistics.mean(protected_times)
                
                assert avg_registration_time < 2.0, f"Registration too slow: {avg_registration_time:.3f}s"
                assert avg_login_time < 1.0, f"Login too slow: {avg_login_time:.3f}s"
                assert avg_protected_time < 0.5, f"Protected endpoint too slow: {avg_protected_time:.3f}s"
                
                # Report performance metrics
                print(f"\nPerformance Benchmarks:")
                print(f"  Registration: {avg_registration_time:.3f}s avg, {max(registration_times):.3f}s max")
                print(f"  Login: {avg_login_time:.3f}s avg, {max(login_times):.3f}s max")
                print(f"  Protected: {avg_protected_time:.3f}s avg, {max(protected_times):.3f}s max")
                
        finally:
            app.user_middleware = original_middleware
            app.dependency_overrides.clear()
    
    def test_concurrent_user_load(self, db_session: Session):
        """Test application performance under concurrent user load."""
        def override_get_db():
            try:
                yield db_session
            finally:
                pass
        
        app.dependency_overrides[get_db] = override_get_db
        
        # Temporarily disable TrustedHostMiddleware
        original_middleware = app.user_middleware
        app.user_middleware = [m for m in app.user_middleware if 'TrustedHostMiddleware' not in str(type(m.cls))]
        
        try:
            with TestClient(app) as client:
                def simulate_user_session(user_id):
                    """Simulate a complete user session."""
                    session_start = time.time()
                    
                    # Register
                    user_data = {"username": f"load_user_{user_id}", "password": f"load_pass_{user_id}123"}
                    register_response = client.post("/api/auth/register", json=user_data)
                    
                    if register_response.status_code != 201:
                        return {"user_id": user_id, "success": False, "stage": "register", "duration": time.time() - session_start}
                    
                    # Login
                    login_response = client.post("/api/auth/login", json=user_data)
                    if login_response.status_code != 200:
                        return {"user_id": user_id, "success": False, "stage": "login", "duration": time.time() - session_start}
                    
                    token = login_response.json()["access_token"]
                    headers = {"Authorization": f"Bearer {token}"}
                    
                    # Access protected endpoint
                    protected_response = client.get("/api/user/protected", headers=headers)
                    if protected_response.status_code != 200:
                        return {"user_id": user_id, "success": False, "stage": "protected", "duration": time.time() - session_start}
                    
                    # Get profile
                    profile_response = client.get("/api/user/profile", headers=headers)
                    if profile_response.status_code != 200:
                        return {"user_id": user_id, "success": False, "stage": "profile", "duration": time.time() - session_start}
                    
                    return {"user_id": user_id, "success": True, "duration": time.time() - session_start}
                
                # Simulate concurrent users
                num_concurrent_users = 10
                with ThreadPoolExecutor(max_workers=num_concurrent_users) as executor:
                    futures = [executor.submit(simulate_user_session, i) for i in range(num_concurrent_users)]
                    results = [future.result() for future in as_completed(futures)]
                
                # Analyze results
                successful_sessions = [r for r in results if r["success"]]
                failed_sessions = [r for r in results if not r["success"]]
                
                success_rate = len(successful_sessions) / len(results) * 100
                avg_session_duration = statistics.mean([r["duration"] for r in successful_sessions]) if successful_sessions else 0
                
                print(f"\nConcurrent Load Test Results:")
                print(f"  Users: {num_concurrent_users}")
                print(f"  Success Rate: {success_rate:.1f}%")
                print(f"  Average Session Duration: {avg_session_duration:.3f}s")
                
                if failed_sessions:
                    print(f"  Failed Sessions: {len(failed_sessions)}")
                    for session in failed_sessions:
                        print(f"    User {session['user_id']}: Failed at {session['stage']}")
                
                # Performance assertions (relaxed for E2E testing)
                assert success_rate >= 70, f"Success rate too low: {success_rate:.1f}%"
                assert avg_session_duration < 10.0, f"Average session too slow: {avg_session_duration:.3f}s"
                
        finally:
            app.user_middleware = original_middleware
            app.dependency_overrides.clear()
    
    def test_memory_usage_under_load(self, db_session: Session):
        """Test memory usage patterns under load."""
        def override_get_db():
            try:
                yield db_session
            finally:
                pass
        
        app.dependency_overrides[get_db] = override_get_db
        
        # Temporarily disable TrustedHostMiddleware
        original_middleware = app.user_middleware
        app.user_middleware = [m for m in app.user_middleware if 'TrustedHostMiddleware' not in str(type(m.cls))]
        
        try:
            import psutil
            import os
            
            with TestClient(app) as client:
                process = psutil.Process(os.getpid())
                initial_memory = process.memory_info().rss / 1024 / 1024  # MB
                
                # Create load to test memory usage
                for i in range(20):
                    user_data = {"username": f"memory_user_{i}", "password": f"memory_pass_{i}123"}
                    
                    # Register
                    client.post("/api/auth/register", json=user_data)
                    
                    # Login
                    login_response = client.post("/api/auth/login", json=user_data)
                    if login_response.status_code == 200:
                        token = login_response.json()["access_token"]
                        headers = {"Authorization": f"Bearer {token}"}
                        
                        # Multiple requests per user
                        for _ in range(5):
                            client.get("/api/user/protected", headers=headers)
                            client.get("/api/user/profile", headers=headers)
                
                final_memory = process.memory_info().rss / 1024 / 1024  # MB
                memory_increase = final_memory - initial_memory
                
                print(f"\nMemory Usage Test:")
                print(f"  Initial Memory: {initial_memory:.2f} MB")
                print(f"  Final Memory: {final_memory:.2f} MB")
                print(f"  Memory Increase: {memory_increase:.2f} MB")
                
                # Memory usage should not increase dramatically
                assert memory_increase < 50, f"Memory increase too high: {memory_increase:.2f} MB"
                
        except ImportError:
            pytest.skip("psutil not available for memory testing")
        finally:
            app.user_middleware = original_middleware
            app.dependency_overrides.clear()


class TestE2ELoadTesting:
    """End-to-end load testing scenarios."""
    
    def test_sustained_load_performance(self, db_session: Session):
        """Test performance under sustained load over time."""
        def override_get_db():
            try:
                yield db_session
            finally:
                pass
        
        app.dependency_overrides[get_db] = override_get_db
        
        # Temporarily disable TrustedHostMiddleware
        original_middleware = app.user_middleware
        app.user_middleware = [m for m in app.user_middleware if 'TrustedHostMiddleware' not in str(type(m.cls))]
        
        try:
            with TestClient(app) as client:
                # Pre-register users for sustained load test
                users = []
                for i in range(5):
                    user_data = {"username": f"sustained_user_{i}", "password": f"sustained_pass_{i}123"}
                    response = client.post("/api/auth/register", json=user_data)
                    assert response.status_code == 201
                    users.append(user_data)
                
                # Get tokens for all users
                tokens = []
                for user_data in users:
                    login_response = client.post("/api/auth/login", json=user_data)
                    assert login_response.status_code == 200
                    tokens.append(login_response.json()["access_token"])
                
                # Sustained load test - make requests over time
                response_times = []
                test_duration = 10  # seconds
                start_time = time.time()
                request_count = 0
                
                while time.time() - start_time < test_duration:
                    for token in tokens:
                        headers = {"Authorization": f"Bearer {token}"}
                        
                        # Measure response time
                        request_start = time.time()
                        response = client.get("/api/user/protected", headers=headers)
                        request_end = time.time()
                        
                        if response.status_code == 200:
                            response_times.append(request_end - request_start)
                            request_count += 1
                        
                        # Small delay to prevent overwhelming
                        time.sleep(0.1)
                
                # Analyze sustained performance
                avg_response_time = statistics.mean(response_times)
                max_response_time = max(response_times)
                requests_per_second = request_count / test_duration
                
                print(f"\nSustained Load Test Results:")
                print(f"  Test Duration: {test_duration}s")
                print(f"  Total Requests: {request_count}")
                print(f"  Requests/Second: {requests_per_second:.2f}")
                print(f"  Average Response Time: {avg_response_time:.3f}s")
                print(f"  Max Response Time: {max_response_time:.3f}s")
                
                # Performance assertions
                assert avg_response_time < 1.0, f"Average response time too slow: {avg_response_time:.3f}s"
                assert max_response_time < 2.0, f"Max response time too slow: {max_response_time:.3f}s"
                assert requests_per_second > 5, f"Throughput too low: {requests_per_second:.2f} req/s"
                
        finally:
            app.user_middleware = original_middleware
            app.dependency_overrides.clear()
    
    def test_spike_load_handling(self, db_session: Session):
        """Test handling of sudden load spikes."""
        def override_get_db():
            try:
                yield db_session
            finally:
                pass
        
        app.dependency_overrides[get_db] = override_get_db
        
        # Temporarily disable TrustedHostMiddleware
        original_middleware = app.user_middleware
        app.user_middleware = [m for m in app.user_middleware if 'TrustedHostMiddleware' not in str(type(m.cls))]
        
        try:
            with TestClient(app) as client:
                def spike_request(request_id):
                    """Make a registration request during spike."""
                    user_data = {"username": f"spike_user_{request_id}", "password": f"spike_pass_{request_id}123"}
                    
                    start_time = time.time()
                    response = client.post("/api/auth/register", json=user_data)
                    end_time = time.time()
                    
                    return {
                        "request_id": request_id,
                        "status_code": response.status_code,
                        "response_time": end_time - start_time,
                        "success": response.status_code == 201
                    }
                
                # Simulate sudden spike in traffic
                spike_size = 15
                with ThreadPoolExecutor(max_workers=spike_size) as executor:
                    spike_start = time.time()
                    futures = [executor.submit(spike_request, i) for i in range(spike_size)]
                    results = [future.result() for future in as_completed(futures)]
                    spike_end = time.time()
                
                # Analyze spike handling
                successful_requests = [r for r in results if r["success"]]
                failed_requests = [r for r in results if not r["success"]]
                
                success_rate = len(successful_requests) / len(results) * 100
                avg_response_time = statistics.mean([r["response_time"] for r in successful_requests]) if successful_requests else 0
                spike_duration = spike_end - spike_start
                
                print(f"\nSpike Load Test Results:")
                print(f"  Spike Size: {spike_size} concurrent requests")
                print(f"  Spike Duration: {spike_duration:.3f}s")
                print(f"  Success Rate: {success_rate:.1f}%")
                print(f"  Average Response Time: {avg_response_time:.3f}s")
                print(f"  Failed Requests: {len(failed_requests)}")
                
                # Spike handling assertions (relaxed for E2E testing)
                assert success_rate >= 60, f"Spike success rate too low: {success_rate:.1f}%"
                assert avg_response_time < 5.0, f"Spike response time too slow: {avg_response_time:.3f}s"
                
        finally:
            app.user_middleware = original_middleware
            app.dependency_overrides.clear()


class TestE2EPerformanceRegression:
    """End-to-end performance regression tests."""
    
    def test_performance_baseline(self, db_session: Session):
        """Establish performance baselines for regression testing."""
        def override_get_db():
            try:
                yield db_session
            finally:
                pass
        
        app.dependency_overrides[get_db] = override_get_db
        
        # Temporarily disable TrustedHostMiddleware
        original_middleware = app.user_middleware
        app.user_middleware = [m for m in app.user_middleware if 'TrustedHostMiddleware' not in str(type(m.cls))]
        
        try:
            with TestClient(app) as client:
                # Baseline measurements
                baseline_metrics = {}
                
                # Registration baseline
                user_data = {"username": "baseline_user", "password": "baseline_pass123"}
                start_time = time.time()
                register_response = client.post("/api/auth/register", json=user_data)
                baseline_metrics["registration_time"] = time.time() - start_time
                assert register_response.status_code == 201
                
                # Login baseline
                start_time = time.time()
                login_response = client.post("/api/auth/login", json=user_data)
                baseline_metrics["login_time"] = time.time() - start_time
                assert login_response.status_code == 200
                
                token = login_response.json()["access_token"]
                headers = {"Authorization": f"Bearer {token}"}
                
                # Protected endpoint baseline
                start_time = time.time()
                protected_response = client.get("/api/user/protected", headers=headers)
                baseline_metrics["protected_time"] = time.time() - start_time
                assert protected_response.status_code == 200
                
                # Profile endpoint baseline
                start_time = time.time()
                profile_response = client.get("/api/user/profile", headers=headers)
                baseline_metrics["profile_time"] = time.time() - start_time
                assert profile_response.status_code == 200
                
                # Token refresh baseline
                start_time = time.time()
                refresh_response = client.post("/api/auth/refresh", headers=headers)
                baseline_metrics["refresh_time"] = time.time() - start_time
                assert refresh_response.status_code == 200
                
                print(f"\nPerformance Baseline Metrics:")
                for metric, value in baseline_metrics.items():
                    print(f"  {metric}: {value:.3f}s")
                
                # Store baselines for future regression tests
                # In a real scenario, these would be stored in a file or database
                expected_baselines = {
                    "registration_time": 2.0,
                    "login_time": 1.0,
                    "protected_time": 0.5,
                    "profile_time": 0.5,
                    "refresh_time": 0.5
                }
                
                # Regression test - ensure we're within expected performance bounds
                for metric, baseline in expected_baselines.items():
                    actual_time = baseline_metrics[metric]
                    assert actual_time <= baseline, f"{metric} regression: {actual_time:.3f}s > {baseline}s"
                
        finally:
            app.user_middleware = original_middleware
            app.dependency_overrides.clear()
