# import requests
# import time
# import statistics
# from urllib.parse import urljoin
# import concurrent.futures
# from threading import Lock
# import argparse
# import sys

# class PhpMyAdminBenchmark:
#     def __init__(self, base_url="http://localhost:8000"):
#         self.base_url = base_url
#         self.session = requests.Session()
#         self.session.headers.update({
#             'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
#         })
#         self.results = []
#         self.lock = Lock()
        
#     def load_urls_from_stage2_out(self, file_path):
#         """Load URLs from stage2_out file"""
#         urls = []
#         try:
#             with open(file_path, 'r') as file:
#                 for line in file:
#                     parts = line.strip().split()
#                     if parts:
#                         url = parts[0]
#                         # Include all URLs from the file
#                         urls.append(url)
#         except Exception as e:
#             print(f"Error loading URLs: {e}")
#         return urls
    
#     def measure_url_response_time(self, url):
#         """Measure response time for a single URL"""
#         try:
#             # Construct full URL
#             if not url.startswith('http'):
#                 full_url = urljoin(self.base_url + '/', url.lstrip('/'))
#             else:
#                 full_url = url
            
#             start_time = time.time()
#             response = self.session.get(full_url, timeout=30, allow_redirects=True)
#             end_time = time.time()
            
#             response_time = end_time - start_time
            
#             result = {
#                 'url': url,
#                 'full_url': full_url,
#                 'status_code': response.status_code,
#                 'response_time': response_time,
#                 'content_length': len(response.content),
#                 'success': response.status_code < 400
#             }
            
#             with self.lock:
#                 self.results.append(result)
            
#             return result
            
#         except Exception as e:
#             result = {
#                 'url': url,
#                 'full_url': full_url if 'full_url' in locals() else url,
#                 'status_code': 0,
#                 'response_time': 0,
#                 'content_length': 0,
#                 'success': False,
#                 'error': str(e)
#             }
            
#             with self.lock:
#                 self.results.append(result)
            
#             return result
    
#     def benchmark_urls(self, urls, max_workers=10):
#         """Benchmark multiple URLs concurrently"""
#         print(f"Starting benchmark for {len(urls)} URLs...")
        
#         with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
#             # Submit all URL requests
#             future_to_url = {executor.submit(self.measure_url_response_time, url): url 
#                            for url in urls}
            
#             # Process completed requests
#             completed = 0
#             for future in concurrent.futures.as_completed(future_to_url):
#                 completed += 1
#                 if completed % 100 == 0:
#                     print(f"Completed {completed}/{len(urls)} requests...")
        
#         print(f"Benchmark completed. Total requests: {len(self.results)}")
    
#     def calculate_statistics(self):
#         """Calculate benchmark statistics"""
#         if not self.results:
#             return None
        
#         successful_results = [r for r in self.results if r['success']]
#         failed_results = [r for r in self.results if not r['success']]
        
#         if not successful_results:
#             print("No successful requests to analyze!")
#             return None
        
#         response_times = [r['response_time'] for r in successful_results]
        
#         stats = {
#             'total_requests': len(self.results),
#             'successful_requests': len(successful_results),
#             'failed_requests': len(failed_results),
#             'success_rate': len(successful_results) / len(self.results) * 100,
#             'avg_response_time': statistics.mean(response_times),
#             'median_response_time': statistics.median(response_times),
#             'min_response_time': min(response_times),
#             'max_response_time': max(response_times),
#             'stdev_response_time': statistics.stdev(response_times) if len(response_times) > 1 else 0
#         }
        
#         return stats
    
#     def print_statistics(self, stats):
#         """Print benchmark statistics"""
#         if not stats:
#             return
        
#         print("\n" + "="*50)
#         print("APPLICATION BENCHMARK RESULTS")
#         print("="*50)
#         print(f"Total Requests: {stats['total_requests']}")
#         print(f"Successful Requests: {stats['successful_requests']}")
#         print(f"Failed Requests: {stats['failed_requests']}")
#         print(f"Success Rate: {stats['success_rate']:.2f}%")
#         print(f"Average Response Time: {stats['avg_response_time']:.4f} seconds")
#         print(f"Median Response Time: {stats['median_response_time']:.4f} seconds")
#         print(f"Min Response Time: {stats['min_response_time']:.4f} seconds")
#         print(f"Max Response Time: {stats['max_response_time']:.4f} seconds")
#         print(f"Standard Deviation: {stats['stdev_response_time']:.4f} seconds")
    
#     def save_detailed_results(self, filename="benchmark_results.txt"):
#         """Save detailed results to file"""
#         with open(filename, 'w') as f:
#             f.write("URL,Status Code,Response Time (s),Content Length,Success\n")
#             for result in self.results:
#                 f.write(f"{result['url']},{result['status_code']},"
#                        f"{result['response_time']:.4f},{result['content_length']},"
#                        f"{result['success']}\n")
#         print(f"Detailed results saved to {filename}")

# def main():
#     # Parse command line arguments
#     parser = argparse.ArgumentParser(description='Benchmark PHP application URLs')
#     parser.add_argument('input_file', help='Path to stage2_out file containing URLs')
#     parser.add_argument('--base-url', default='http://localhost:8000', 
#                        help='Base URL for the application (default: http://localhost:8000)')
#     parser.add_argument('--workers', type=int, default=5,
#                        help='Number of concurrent workers (default: 5)')
#     parser.add_argument('--output', default='benchmark_results.txt',
#                        help='Output file for detailed results (default: benchmark_results.txt)')
    
#     args = parser.parse_args()
    
#     # Check if input file exists
#     try:
#         with open(args.input_file, 'r') as f:
#             pass
#     except FileNotFoundError:
#         print(f"Error: Input file '{args.input_file}' not found!")
#         sys.exit(1)
    
#     # Initialize benchmark
#     benchmark = PhpMyAdminBenchmark(base_url=args.base_url)
    
#     # Load URLs from stage2_out file
#     urls = benchmark.load_urls_from_stage2_out(args.input_file)
    
#     if not urls:
#         print("No URLs found in stage2_out file!")
#         return
    
#     print(f"Loaded {len(urls)} URLs from {args.input_file}")
#     print(f"Base URL: {args.base_url}")
#     print(f"Workers: {args.workers}")
    
#     # Run benchmark
#     benchmark.benchmark_urls(urls, max_workers=args.workers)
    
#     # Calculate and print statistics
#     stats = benchmark.calculate_statistics()
#     benchmark.print_statistics(stats)
    
#     # Save detailed results
#     benchmark.save_detailed_results(args.output)
    
#     # Print some sample failed requests for debugging
#     failed_requests = [r for r in benchmark.results if not r['success']]
#     if failed_requests:
#         print(f"\nSample failed requests ({min(5, len(failed_requests))}):")
#         for i, req in enumerate(failed_requests[:5]):
#             error_msg = req.get('error', 'Unknown error')
#             print(f"  {i+1}. {req['url']} - {error_msg}")

# if __name__ == "__main__":
#     main()
import requests
import time
import statistics
from urllib.parse import urljoin
import concurrent.futures
from threading import Lock
import argparse
import sys

class PhpMyAdminBenchmark:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
        })
        self.results = []
        self.lock = Lock()
        
    def load_urls_from_stage2_out(self, file_path):
        """Load URLs from stage2_out file"""
        urls = []
        try:
            with open(file_path, 'r') as file:
                for line in file:
                    parts = line.strip().split()
                    if parts:
                        url = parts[0]
                        # Include all URLs from the file
                        urls.append(url)
        except Exception as e:
            print(f"Error loading URLs: {e}")
        return urls
    
    def measure_url_response_time(self, url):
        """Measure response time for a single URL"""
        try:
            # Construct full URL
            if not url.startswith('http'):
                full_url = urljoin(self.base_url + '/', url.lstrip('/'))
            else:
                full_url = url
            
            start_time = time.time()
            response = self.session.get(full_url, timeout=30, allow_redirects=True)
            end_time = time.time()
            
            response_time = end_time - start_time
            
            result = {
                'url': url,
                'full_url': full_url,
                'status_code': response.status_code,
                'response_time': response_time,
                'content_length': len(response.content),
                'success': response.status_code < 400
            }
            
            with self.lock:
                self.results.append(result)
            
            return result
            
        except Exception as e:
            result = {
                'url': url,
                'full_url': full_url if 'full_url' in locals() else url,
                'status_code': 0,
                'response_time': 0,
                'content_length': 0,
                'success': False,
                'error': str(e)
            }
            
            with self.lock:
                self.results.append(result)
            
            return result
    
    def benchmark_urls(self, urls, max_workers=10):
        """Benchmark multiple URLs concurrently"""
        print(f"Starting benchmark for {len(urls)} URLs...")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all URL requests
            future_to_url = {executor.submit(self.measure_url_response_time, url): url 
                           for url in urls}
            
            # Process completed requests
            completed = 0
            for future in concurrent.futures.as_completed(future_to_url):
                completed += 1
                if completed % 100 == 0:
                    print(f"Completed {completed}/{len(urls)} requests...")
        
        print(f"Benchmark completed. Total requests: {len(self.results)}")
    
    def parallel_load_test(self, url="/index.php", total_requests=15000, parallel_levels=[1, 2, 4, 8, 16, 32]):
        """
        Run parallel load test with different concurrency levels
        
        Args:
            url (str): URL to test (default: /index.php)
            total_requests (int): Total number of requests per parallel level
            parallel_levels (list): List of concurrency levels to test
        """
        print(f"\n{'='*60}")
        print("PARALLEL LOAD TEST")
        print(f"{'='*60}")
        print(f"Target URL: {url}")
        print(f"Requests per level: {total_requests}")
        print(f"Parallel levels: {parallel_levels}")
        print(f"{'='*60}")
        
        all_results = {}
        
        for workers in parallel_levels:
            print(f"\nTesting with {workers} parallel worker(s)...")
            
            # Reset results for this test
            self.results = []
            
            # Create URL list for this test
            test_urls = [url] * total_requests
            
            # Record start time for total duration
            test_start_time = time.time()
            
            # Run the benchmark
            with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
                # Submit all requests
                futures = [executor.submit(self.measure_url_response_time, url) for url in test_urls]
                
                # Track progress
                completed = 0
                for future in concurrent.futures.as_completed(futures):
                    completed += 1
                    if completed % 1000 == 0:
                        print(f"  Progress: {completed}/{total_requests} requests completed...")
            
            test_end_time = time.time()
            total_test_duration = test_end_time - test_start_time
            
            # Calculate statistics for this parallel level
            stats = self.calculate_statistics()
            if stats:
                stats['workers'] = workers
                stats['total_test_duration'] = total_test_duration
                stats['requests_per_second'] = total_requests / total_test_duration
                all_results[workers] = stats
                
                print(f"  Completed in {total_test_duration:.2f} seconds")
                print(f"  Requests/second: {stats['requests_per_second']:.2f}")
                print(f"  Average response time: {stats['avg_response_time']:.4f}s ({stats['avg_response_time']*1000:.2f}ms)")
                print(f"  Success rate: {stats['success_rate']:.2f}%")
        
        # Print comprehensive results
        self.print_parallel_test_results(all_results)
        
        # Save results to file
        self.save_parallel_test_results(all_results)
        
        return all_results
    
    def print_parallel_test_results(self, all_results):
        """Print comprehensive parallel test results"""
        print(f"\n{'='*80}")
        print("PARALLEL LOAD TEST SUMMARY")
        print(f"{'='*80}")
        
        # Header
        print(f"{'Workers':<8} {'Req/sec':<10} {'Avg Time(ms)':<12} {'Min(ms)':<8} {'Max(ms)':<8} {'Success%':<9} {'Total Time(s)':<12}")
        print("-" * 80)
        
        # Results for each parallel level
        for workers in sorted(all_results.keys()):
            stats = all_results[workers]
            print(f"{workers:<8} "
                  f"{stats['requests_per_second']:<10.2f} "
                  f"{stats['avg_response_time']*1000:<12.2f} "
                  f"{stats['min_response_time']*1000:<8.2f} "
                  f"{stats['max_response_time']*1000:<8.2f} "
                  f"{stats['success_rate']:<9.2f} "
                  f"{stats['total_test_duration']:<12.2f}")
        
        print("-" * 80)
        
        # Find best performing configuration
        best_throughput = max(all_results.items(), key=lambda x: x[1]['requests_per_second'])
        best_latency = min(all_results.items(), key=lambda x: x[1]['avg_response_time'])
        
        print(f"\nBest Throughput: {best_throughput[1]['requests_per_second']:.2f} req/s at {best_throughput[0]} workers")
        print(f"Best Latency: {best_latency[1]['avg_response_time']*1000:.2f}ms at {best_latency[0]} workers")
    
    def save_parallel_test_results(self, all_results, filename="parallel_test_results.csv"):
        """Save parallel test results to CSV file"""
        with open(filename, 'w') as f:
            f.write("Workers,Requests_Per_Second,Avg_Response_Time_ms,Min_Response_Time_ms,Max_Response_Time_ms,Success_Rate,Total_Test_Duration_s,Total_Requests,Successful_Requests,Failed_Requests\n")
            
            for workers in sorted(all_results.keys()):
                stats = all_results[workers]
                f.write(f"{workers},"
                       f"{stats['requests_per_second']:.2f},"
                       f"{stats['avg_response_time']*1000:.2f},"
                       f"{stats['min_response_time']*1000:.2f},"
                       f"{stats['max_response_time']*1000:.2f},"
                       f"{stats['success_rate']:.2f},"
                       f"{stats['total_test_duration']:.2f},"
                       f"{stats['total_requests']},"
                       f"{stats['successful_requests']},"
                       f"{stats['failed_requests']}\n")
        
        print(f"\nDetailed results saved to {filename}")
    
    def calculate_statistics(self):
        """Calculate benchmark statistics"""
        if not self.results:
            return None
        
        successful_results = [r for r in self.results if r['success']]
        failed_results = [r for r in self.results if not r['success']]
        
        if not successful_results:
            print("No successful requests to analyze!")
            return None
        
        response_times = [r['response_time'] for r in successful_results]
        
        stats = {
            'total_requests': len(self.results),
            'successful_requests': len(successful_results),
            'failed_requests': len(failed_results),
            'success_rate': len(successful_results) / len(self.results) * 100,
            'avg_response_time': statistics.mean(response_times),
            'median_response_time': statistics.median(response_times),
            'min_response_time': min(response_times),
            'max_response_time': max(response_times),
            'stdev_response_time': statistics.stdev(response_times) if len(response_times) > 1 else 0
        }
        
        return stats
    
    def print_statistics(self, stats):
        """Print benchmark statistics"""
        if not stats:
            return
        
        print("\n" + "="*50)
        print("APPLICATION BENCHMARK RESULTS")
        print("="*50)
        print(f"Total Requests: {stats['total_requests']}")
        print(f"Successful Requests: {stats['successful_requests']}")
        print(f"Failed Requests: {stats['failed_requests']}")
        print(f"Success Rate: {stats['success_rate']:.2f}%")
        print(f"Average Response Time: {stats['avg_response_time']:.4f} seconds ({stats['avg_response_time']*1000:.2f} ms)")
        print(f"Median Response Time: {stats['median_response_time']:.4f} seconds ({stats['median_response_time']*1000:.2f} ms)")
        print(f"Min Response Time: {stats['min_response_time']:.4f} seconds ({stats['min_response_time']*1000:.2f} ms)")
        print(f"Max Response Time: {stats['max_response_time']:.4f} seconds ({stats['max_response_time']*1000:.2f} ms)")
        print(f"Standard Deviation: {stats['stdev_response_time']:.4f} seconds")
    
    def save_detailed_results(self, filename="benchmark_results.txt"):
        """Save detailed results to file"""
        with open(filename, 'w') as f:
            f.write("URL,Status Code,Response Time (s),Response Time (ms),Content Length,Success\n")
            for result in self.results:
                f.write(f"{result['url']},{result['status_code']},"
                       f"{result['response_time']:.4f},{result['response_time']*1000:.2f},"
                       f"{result['content_length']},{result['success']}\n")
        print(f"Detailed results saved to {filename}")

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Benchmark PHP application URLs')
    parser.add_argument('input_file', nargs='?', help='Path to stage2_out file containing URLs')
    parser.add_argument('--base-url', default='http://localhost:8000', 
                       help='Base URL for the application (default: http://localhost:8000)')
    parser.add_argument('--workers', type=int, default=5,
                       help='Number of concurrent workers (default: 5)')
    parser.add_argument('--output', default='benchmark_results.txt',
                       help='Output file for detailed results (default: benchmark_results.txt)')
    
    # Parallel testing options
    parser.add_argument('--parallel-test', action='store_true',
                       help='Run parallel load test instead of regular benchmark')
    parser.add_argument('--test-url', default='/index.php',
                       help='URL to test in parallel mode (default: /index.php)')
    parser.add_argument('--requests', type=int, default=15000,
                       help='Total requests per parallel level (default: 15000)')
    parser.add_argument('--parallel-levels', nargs='+', type=int, default=[1, 2, 4, 8, 16, 32],
                       help='Parallel levels to test (default: 1 2 4 8 16 32)')
    
    args = parser.parse_args()
    
    # Initialize benchmark
    benchmark = PhpMyAdminBenchmark(base_url=args.base_url)
    
    if args.parallel_test:
        # Run parallel load test
        print(f"Running parallel load test...")
        print(f"Base URL: {args.base_url}")
        print(f"Test URL: {args.test_url}")
        print(f"Requests per level: {args.requests}")
        print(f"Parallel levels: {args.parallel_levels}")
        
        results = benchmark.parallel_load_test(
            url=args.test_url,
            total_requests=args.requests,
            parallel_levels=args.parallel_levels
        )
        
    else:
        # Regular benchmark mode
        if not args.input_file:
            print("Error: input_file is required for regular benchmark mode!")
            sys.exit(1)
        
        # Check if input file exists
        try:
            with open(args.input_file, 'r') as f:
                pass
        except FileNotFoundError:
            print(f"Error: Input file '{args.input_file}' not found!")
            sys.exit(1)
        
        # Load URLs from stage2_out file
        urls = benchmark.load_urls_from_stage2_out(args.input_file)
        
        if not urls:
            print("No URLs found in stage2_out file!")
            return
        
        print(f"Loaded {len(urls)} URLs from {args.input_file}")
        print(f"Base URL: {args.base_url}")
        print(f"Workers: {args.workers}")
        
        # Run benchmark
        benchmark.benchmark_urls(urls, max_workers=args.workers)
        
        # Calculate and print statistics
        stats = benchmark.calculate_statistics()
        benchmark.print_statistics(stats)
        
        # Save detailed results
        benchmark.save_detailed_results(args.output)
        
        # Print some sample failed requests for debugging
        failed_requests = [r for r in benchmark.results if not r['success']]
        if failed_requests:
            print(f"\nSample failed requests ({min(5, len(failed_requests))}):")
            for i, req in enumerate(failed_requests[:5]):
                error_msg = req.get('error', 'Unknown error')
                print(f"  {i+1}. {req['url']} - {error_msg}")

if __name__ == "__main__":
    main()