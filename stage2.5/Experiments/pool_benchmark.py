# import requests
# import time
# import statistics
# from urllib.parse import urljoin
# import concurrent.futures
# from threading import Lock
# import argparse
# import sys
# import os
# import re
# import json

# class PoolBenchmark:
#     def __init__(self, base_url="http://localhost:8000"):
#         self.base_url = base_url
#         self.session = requests.Session()
#         self.session.headers.update({
#             'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
#         })
#         self.results = []
#         self.lock = Lock()
        
#     def get_pools_from_nginx_configs(self, nginx_config_dir='nginx-url-map-files'):
#         """Extract pools and their URLs from nginx config files"""
#         pools = {}
        
#         if not os.path.exists(nginx_config_dir):
#             print(f"Error: {nginx_config_dir} not found!")
#             return pools
        
#         # Read each url_map config file
#         for filename in sorted(os.listdir(nginx_config_dir)):
#             if filename.startswith('url_map_') and filename.endswith('.conf'):
#                 pool_num = filename.replace('url_map_', '').replace('.conf', '')
                
#                 with open(os.path.join(nginx_config_dir, filename), 'r') as f:
#                     content = f.read()
                    
#                 # Extract URLs from the config file
#                 # Format: "URL unix:/opt/php-7.1/var/run/php/pool_X.sock;"
#                 urls = re.findall(r'([^\s]+)\s+unix:/opt/php-7\.1/var/run/php/pool_(\d+)\.sock;', content)
#                 pool_urls = [url for url, pool_id in urls if pool_id == pool_num]
                
#                 if pool_urls:
#                     pools[f"pool_{pool_num}"] = pool_urls
                    
#         return pools
    
#     def select_popular_urls_from_pools(self, pools, app_name):
#         """Select popular URLs from each pool based on application type"""
        
#         # Define popular URL patterns for different applications
#         popular_patterns = {
#             'wordpress': [
#                 'index.php', 'wp-admin/index.php', 'wp-login.php', 'wp-admin/admin.php',
#                 'wp-admin/post.php', 'wp-admin/edit.php', 'wp-content/themes/',
#                 'wp-includes/js/', 'wp-admin/admin-ajax.php'
#             ],
#             'phpmyadmin': [
#                 'index.php', 'main.php', 'db_structure.php', 'tbl_structure.php',
#                 'sql.php', 'import.php', 'export.php', 'server_status.php'
#             ],
#             'moodle': [
#                 'index.php', 'login/index.php', 'course/view.php', 'mod/quiz/view.php',
#                 'user/profile.php', 'admin/index.php', 'my/index.php'
#             ],
#             'drupal': [
#                 'index.php', 'admin/index.php', 'node/add', 'user/login',
#                 'admin/structure', 'admin/config', 'admin/content'
#             ],
#             'joomla': [
#                 'index.php', 'administrator/index.php', 'administrator/components/',
#                 'components/com_content/', 'modules/', 'templates/'
#             ]
#         }
        
#         app_patterns = popular_patterns.get(app_name, ['index.php'])
#         selected_urls = {}
        
#         for pool_name, pool_urls in pools.items():
#             # Try to find popular URLs in this pool
#             pool_selected = []
            
#             # Look for each popular pattern
#             for pattern in app_patterns:
#                 matching_urls = [url for url in pool_urls if pattern in url]
#                 if matching_urls:
#                     # Take the first match for each pattern
#                     pool_selected.append(matching_urls[0])
#                     if len(pool_selected) >= 3:  # Limit to 3 URLs per pool
#                         break
            
#             # If no popular URLs found, take the first few URLs
#             if not pool_selected:
#                 pool_selected = pool_urls[:min(3, len(pool_urls))]
            
#             # If still no URLs, use a default
#             if not pool_selected:
#                 pool_selected = ['index.php']
            
#             selected_urls[pool_name] = pool_selected
            
#         return selected_urls
    
#     def measure_url_response_time(self, url_info):
#         """Measure response time for a single URL"""
#         pool_name, url = url_info
        
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
#                 'pool': pool_name,
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
#                 'pool': pool_name,
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
    
#     def run_pool_benchmark(self, selected_urls, total_requests=15000, parallel_levels=[1, 2, 4, 8, 16, 32]):
#         """Run benchmark test for selected URLs from each pool"""
        
#         print(f"\n{'='*80}")
#         print("POOL-BASED PARALLEL LOAD TEST")
#         print(f"{'='*80}")
#         print(f"Pools and URLs to test:")
#         for pool_name, urls in selected_urls.items():
#             print(f"  {pool_name}: {urls}")
#         print(f"Requests per level: {total_requests}")
#         print(f"Parallel levels: {parallel_levels}")
#         print(f"{'='*80}")
        
#         # Create URL list for testing (distribute requests across all selected URLs)
#         test_urls = []
#         url_pool_map = []
        
#         for pool_name, urls in selected_urls.items():
#             for url in urls:
#                 test_urls.append(url)
#                 url_pool_map.append((pool_name, url))
        
#         all_results = {}
        
#         for workers in parallel_levels:
#             print(f"\nTesting with {workers} parallel worker(s)...")
            
#             # Reset results for this test
#             self.results = []
            
#             # Create request list by cycling through URLs
#             request_list = []
#             for i in range(total_requests):
#                 url_index = i % len(url_pool_map)
#                 request_list.append(url_pool_map[url_index])
            
#             # Record start time for total duration
#             test_start_time = time.time()
            
#             # Run the benchmark
#             with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
#                 # Submit all requests
#                 futures = [executor.submit(self.measure_url_response_time, url_info) for url_info in request_list]
                
#                 # Track progress
#                 completed = 0
#                 for future in concurrent.futures.as_completed(futures):
#                     completed += 1
#                     if completed % 1000 == 0:
#                         print(f"  Progress: {completed}/{total_requests} requests completed...")
            
#             test_end_time = time.time()
#             total_test_duration = test_end_time - test_start_time
            
#             # Calculate statistics for this parallel level
#             stats = self.calculate_statistics()
#             if stats:
#                 stats['workers'] = workers
#                 stats['total_test_duration'] = total_test_duration
#                 stats['requests_per_second'] = total_requests / total_test_duration
                
#                 # Calculate per-pool statistics
#                 pool_stats = self.calculate_pool_statistics()
#                 stats['pool_stats'] = pool_stats
                
#                 all_results[workers] = stats
                
#                 print(f"  Completed in {total_test_duration:.2f} seconds")
#                 print(f"  Requests/second: {stats['requests_per_second']:.2f}")
#                 print(f"  Average response time: {stats['avg_response_time']:.4f}s ({stats['avg_response_time']*1000:.2f}ms)")
#                 print(f"  Success rate: {stats['success_rate']:.2f}%")
        
#         # Print comprehensive results
#         self.print_pool_test_results(all_results, selected_urls)
        
#         # Save results to files
#         self.save_pool_test_results(all_results, selected_urls)
        
#         return all_results
    
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
    
#     def calculate_pool_statistics(self):
#         """Calculate statistics per pool"""
#         pool_stats = {}
        
#         # Group results by pool
#         for result in self.results:
#             if result['success']:
#                 pool = result['pool']
#                 if pool not in pool_stats:
#                     pool_stats[pool] = []
#                 pool_stats[pool].append(result['response_time'])
        
#         # Calculate stats for each pool
#         pool_summary = {}
#         for pool, response_times in pool_stats.items():
#             if response_times:
#                 pool_summary[pool] = {
#                     'count': len(response_times),
#                     'avg_response_time': statistics.mean(response_times),
#                     'min_response_time': min(response_times),
#                     'max_response_time': max(response_times)
#                 }
        
#         return pool_summary
    
#     def print_pool_test_results(self, all_results, selected_urls):
#         """Print comprehensive pool test results"""
#         print(f"\n{'='*100}")
#         print("POOL-BASED LOAD TEST SUMMARY")
#         print(f"{'='*100}")
        
#         # Header
#         print(f"{'Workers':<8} {'Req/sec':<10} {'Avg Time(ms)':<12} {'Min(ms)':<8} {'Max(ms)':<8} {'Success%':<9} {'Total Time(s)':<12}")
#         print("-" * 100)
        
#         # Results for each parallel level
#         for workers in sorted(all_results.keys()):
#             stats = all_results[workers]
#             print(f"{workers:<8} "
#                   f"{stats['requests_per_second']:<10.2f} "
#                   f"{stats['avg_response_time']*1000:<12.2f} "
#                   f"{stats['min_response_time']*1000:<8.2f} "
#                   f"{stats['max_response_time']*1000:<8.2f} "
#                   f"{stats['success_rate']:<9.2f} "
#                   f"{stats['total_test_duration']:<12.2f}")
        
#         print("-" * 100)
        
#         # Per-pool performance (show for highest concurrency level)
#         if all_results:
#             highest_concurrency = max(all_results.keys())
#             pool_stats = all_results[highest_concurrency].get('pool_stats', {})
            
#             if pool_stats:
#                 print(f"\nPer-Pool Performance (at {highest_concurrency} workers):")
#                 print(f"{'Pool':<15} {'Requests':<10} {'Avg Time(ms)':<12} {'Min(ms)':<8} {'Max(ms)':<8}")
#                 print("-" * 60)
                
#                 for pool, stats in pool_stats.items():
#                     print(f"{pool:<15} "
#                           f"{stats['count']:<10} "
#                           f"{stats['avg_response_time']*1000:<12.2f} "
#                           f"{stats['min_response_time']*1000:<8.2f} "
#                           f"{stats['max_response_time']*1000:<8.2f}")
        
#         # Find best performing configuration
#         best_throughput = max(all_results.items(), key=lambda x: x[1]['requests_per_second'])
#         best_latency = min(all_results.items(), key=lambda x: x[1]['avg_response_time'])
        
#         print(f"\nBest Throughput: {best_throughput[1]['requests_per_second']:.2f} req/s at {best_throughput[0]} workers")
#         print(f"Best Latency: {best_latency[1]['avg_response_time']*1000:.2f}ms at {best_latency[0]} workers")
    
#     def save_pool_test_results(self, all_results, selected_urls):
#         """Save pool test results to files"""
        
#         # Save summary results
#         summary_filename = "pool_benchmark_summary.csv"
#         with open(summary_filename, 'w') as f:
#             f.write("Workers,Requests_Per_Second,Avg_Response_Time_ms,Min_Response_Time_ms,Max_Response_Time_ms,Success_Rate,Total_Test_Duration_s\n")
            
#             for workers in sorted(all_results.keys()):
#                 stats = all_results[workers]
#                 f.write(f"{workers},"
#                        f"{stats['requests_per_second']:.2f},"
#                        f"{stats['avg_response_time']*1000:.2f},"
#                        f"{stats['min_response_time']*1000:.2f},"
#                        f"{stats['max_response_time']*1000:.2f},"
#                        f"{stats['success_rate']:.2f},"
#                        f"{stats['total_test_duration']:.2f}\n")
        
#         # Save detailed results
#         detailed_filename = "pool_benchmark_detailed.csv"
#         with open(detailed_filename, 'w') as f:
#             f.write("Workers,Pool,URL,Status_Code,Response_Time_ms,Content_Length,Success\n")
            
#             for workers in sorted(all_results.keys()):
#                 # Save a sample of results for each worker level
#                 worker_results = [r for r in self.results if 'workers' not in r or r.get('workers') == workers]
#                 for result in worker_results[:1000]:  # Limit to first 1000 results per worker level
#                     f.write(f"{workers},"
#                            f"{result['pool']},"
#                            f"{result['url']},"
#                            f"{result['status_code']},"
#                            f"{result['response_time']*1000:.2f},"
#                            f"{result['content_length']},"
#                            f"{result['success']}\n")
        
#         # Save pool configuration
#         config_filename = "pool_configuration.json"
#         with open(config_filename, 'w') as f:
#             json.dump(selected_urls, f, indent=2)
        
#         print(f"\nResults saved to:")
#         print(f"  - {summary_filename}")
#         print(f"  - {detailed_filename}")
#         print(f"  - {config_filename}")

# def main():
#     parser = argparse.ArgumentParser(description='Pool-based parallel load testing')
#     parser.add_argument('--app', type=str, required=True,
#                        choices=['wordpress', 'phpmyadmin', 'moodle', 'drupal', 'joomla'],
#                        help='Application name')
#     parser.add_argument('--base-url', default='http://localhost:8000',
#                        help='Base URL for the application (default: http://localhost:8000)')
#     parser.add_argument('--requests', type=int, default=15000,
#                        help='Total requests per parallel level (default: 15000)')
#     parser.add_argument('--parallel-levels', nargs='+', type=int, default=[1, 2, 4, 8, 16, 32],
#                        help='Parallel levels to test (default: 1 2 4 8 16 32)')
#     parser.add_argument('--nginx-config-dir', default='nginx-url-map-files',
#                        help='Directory containing nginx URL map files')
    
#     args = parser.parse_args()
    
#     # Initialize benchmark
#     benchmark = PoolBenchmark(base_url=args.base_url)
    
#     # Get pools from nginx config files
#     pools = benchmark.get_pools_from_nginx_configs(args.nginx_config_dir)
    
#     if not pools:
#         print("No pools found! Make sure you've run the mpool configuration first.")
#         sys.exit(1)
    
#     print(f"Found {len(pools)} pools:")
#     for pool_name, urls in pools.items():
#         print(f"  {pool_name}: {len(urls)} URLs")
    
#     # Select popular URLs from each pool
#     selected_urls = benchmark.select_popular_urls_from_pools(pools, args.app)
    
#     # Run the benchmark
#     results = benchmark.run_pool_benchmark(
#         selected_urls=selected_urls,
#         total_requests=args.requests,
#         parallel_levels=args.parallel_levels
#     )

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
import os
import re
import json

class PoolBenchmark:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
        })
        self.results = []
        self.lock = Lock()
        
    def get_pools_from_nginx_configs(self, nginx_config_dir='nginx-url-map-files'):
        """Extract pools and their URLs from nginx config files"""
        pools = {}
        
        if not os.path.exists(nginx_config_dir):
            print(f"Error: {nginx_config_dir} not found!")
            return pools
        
        # Read each url_map config file
        for filename in sorted(os.listdir(nginx_config_dir)):
            if filename.startswith('url_map_') and filename.endswith('.conf'):
                pool_num = filename.replace('url_map_', '').replace('.conf', '')
                
                with open(os.path.join(nginx_config_dir, filename), 'r') as f:
                    lines = f.readlines()
                    
                # Extract URLs from each line
                # Format: "URL unix:/opt/php-7.1/var/run/php/pool_X.sock;"
                pool_urls = []
                for line in lines:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        # Split by whitespace and take the first part (URL)
                        parts = line.split()
                        if len(parts) >= 2 and f'pool_{pool_num}.sock' in parts[1]:
                            pool_urls.append(parts[0])
                
                if pool_urls:
                    pools[f"pool_{pool_num}"] = pool_urls
                    
        return pools
    
    def get_default_pool_urls(self, app_name):
        """Get URLs that belong to the default pool (exact intersection set)"""
        try:
            # Import intersection module functions
            sys.path.append('/home/paper/stage2.5')
            import intersection as its
            
            # Get the stage2_out file path
            file_path = f'/home/paper/stage2_out_{app_name}'
            if not os.path.exists(file_path):
                file_path = f'stage2_out_backup/stage2_out_{app_name}'
            
            if not os.path.exists(file_path):
                print(f"Warning: Could not find stage2_out file for {app_name}")
                return []
            
            # Recreate the categorization process
            categorized_urls = its.categorize_urls_by_numbers(file_path)
            intersection = its.intersection_of_urls(categorized_urls)
            
            # Get URLs with exact intersection set (these go to default pool)
            default_urls = its.calculate_urls_with_exact_intersection_set(categorized_urls, intersection)
            
            return default_urls
            
        except Exception as e:
            print(f"Error getting default pool URLs: {e}")
            return []

    def get_all_pools_including_default(self, nginx_config_dir='nginx-url-map-files', app_name=None):
        """Get all pools including the default pool"""
        
        # Get pools from nginx config files
        pools = self.get_pools_from_nginx_configs(nginx_config_dir)
        
        # Get default pool URLs
        if app_name:
            default_urls = self.get_default_pool_urls(app_name)
            if default_urls:
                # Find the highest pool number and add 1 for default pool
                if pools:
                    pool_numbers = [int(name.replace('pool_', '')) for name in pools.keys()]
                    default_pool_num = max(pool_numbers) + 1
                else:
                    default_pool_num = 1
                
                pools[f"pool_{default_pool_num}_default"] = default_urls
                print(f"Added default pool with {len(default_urls)} URLs")
        
        return pools
    
    def select_one_url_per_pool(self, pools, app_name):
        """Select only one popular URL from each pool based on application type"""
        
        # Define popular URL patterns for different applications (in priority order)
        popular_patterns = {
            'wordpress': [
                'index.php', 'wp-admin/index.php', 'wp-login.php', 'wp-admin/admin.php',
                'wp-admin/post.php', 'wp-admin/edit.php', 'wp-content/themes/',
                'wp-includes/js/', 'wp-admin/admin-ajax.php'
            ],
            'phpmyadmin': [
                'index.php', 'main.php', 'db_structure.php', 'tbl_structure.php',
                'sql.php', 'import.php', 'export.php', 'server_status.php'
            ],
            'moodle': [
                'index.php', 'login/index.php', 'course/view.php', 'mod/quiz/view.php',
                'user/profile.php', 'admin/index.php', 'my/index.php'
            ],
            'drupal': [
                'index.php', 'admin/index.php', 'node/add', 'user/login',
                'admin/structure', 'admin/config', 'admin/content'
            ],
            'joomla': [
                'index.php', 'administrator/index.php', 'administrator/components/',
                'components/com_content/', 'modules/', 'templates/'
            ]
        }
        
        app_patterns = popular_patterns.get(app_name, ['index.php'])
        selected_urls = {}
        
        for pool_name, pool_urls in pools.items():
            # Try to find the first popular URL in this pool
            selected_url = None
            
            # Special handling for default pool - prefer index.php
            if 'default' in pool_name:
                # For default pool, prioritize index.php or main entry points
                priority_patterns = ['index.php', 'main.php']
                for pattern in priority_patterns:
                    matching_urls = [url for url in pool_urls if pattern in url]
                    if matching_urls:
                        selected_url = matching_urls[0]
                        break
            
            # If not found yet, look for popular patterns
            if not selected_url:
                for pattern in app_patterns:
                    matching_urls = [url for url in pool_urls if pattern in url]
                    if matching_urls:
                        selected_url = matching_urls[0]  # Take the first match
                        break
            
            # If no popular URL found, take the first URL from the pool
            if not selected_url:
                selected_url = pool_urls[0] if pool_urls else 'index.php'
            
            # Store as a single-item list for consistency with existing code
            selected_urls[pool_name] = [selected_url]
            
        return selected_urls
    
    def measure_url_response_time(self, url_info):
        """Measure response time for a single URL"""
        pool_name, url = url_info
        
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
                'pool': pool_name,
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
                'pool': pool_name,
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
    
    def run_pool_benchmark(self, selected_urls, total_requests=15000, parallel_levels=[1, 2, 4, 8, 16, 32]):
        """Run benchmark test for selected URLs from each pool"""
        
        print(f"\n{'='*80}")
        print("POOL-BASED PARALLEL LOAD TEST (ONE URL PER POOL)")
        print(f"{'='*80}")
        print(f"Pools and URLs to test:")
        for pool_name, urls in selected_urls.items():
            pool_type = " (DEFAULT)" if 'default' in pool_name else ""
            print(f"  {pool_name}{pool_type}: {urls[0]}")  # Only show the single URL
        print(f"Requests per level: {total_requests}")
        print(f"Parallel levels: {parallel_levels}")
        print(f"{'='*80}")
        
        # Create URL list for testing (one URL per pool)
        url_pool_map = []
        
        for pool_name, urls in selected_urls.items():
            # Only take the first (and only) URL from each pool
            url_pool_map.append((pool_name, urls[0]))
        
        all_results = {}
        
        for workers in parallel_levels:
            print(f"\nTesting with {workers} parallel worker(s)...")
            
            # Reset results for this test
            self.results = []
            
            # Create request list by cycling through pool URLs
            request_list = []
            for i in range(total_requests):
                url_index = i % len(url_pool_map)
                request_list.append(url_pool_map[url_index])
            
            # Record start time for total duration
            test_start_time = time.time()
            
            # Run the benchmark
            with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
                # Submit all requests
                futures = [executor.submit(self.measure_url_response_time, url_info) for url_info in request_list]
                
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
                
                # Calculate per-pool statistics
                pool_stats = self.calculate_pool_statistics()
                stats['pool_stats'] = pool_stats
                
                all_results[workers] = stats
                
                print(f"  Completed in {total_test_duration:.2f} seconds")
                print(f"  Requests/second: {stats['requests_per_second']:.2f}")
                print(f"  Average response time: {stats['avg_response_time']:.4f}s ({stats['avg_response_time']*1000:.2f}ms)")
                print(f"  Success rate: {stats['success_rate']:.2f}%")
        
        # Print comprehensive results
        self.print_pool_test_results(all_results, selected_urls)
        
        # Save results to files
        self.save_pool_test_results(all_results, selected_urls)
        
        return all_results
    
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
    
    def calculate_pool_statistics(self):
        """Calculate statistics per pool"""
        pool_stats = {}
        
        # Group results by pool
        for result in self.results:
            if result['success']:
                pool = result['pool']
                if pool not in pool_stats:
                    pool_stats[pool] = []
                pool_stats[pool].append(result['response_time'])
        
        # Calculate stats for each pool
        pool_summary = {}
        for pool, response_times in pool_stats.items():
            if response_times:
                pool_summary[pool] = {
                    'count': len(response_times),
                    'avg_response_time': statistics.mean(response_times),
                    'min_response_time': min(response_times),
                    'max_response_time': max(response_times),
                    'stdev_response_time': statistics.stdev(response_times) if len(response_times) > 1 else 0
                }
        
        return pool_summary
    
    def print_pool_test_results(self, all_results, selected_urls):
        """Print comprehensive pool test results"""
        print(f"\n{'='*100}")
        print("POOL-BASED LOAD TEST SUMMARY (ONE URL PER POOL)")
        print(f"{'='*100}")
        
        # Show which URL was selected for each pool
        print("Selected URLs per pool:")
        for pool_name, urls in selected_urls.items():
            pool_type = " (DEFAULT)" if 'default' in pool_name else ""
            print(f"  {pool_name}{pool_type}: {urls[0]}")
        print()
        
        # Header
        print(f"{'Workers':<8} {'Req/sec':<10} {'Avg Time(ms)':<12} {'Min(ms)':<8} {'Max(ms)':<8} {'Success%':<9} {'Total Time(s)':<12}")
        print("-" * 100)
        
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
        
        print("-" * 100)
        
        # Per-pool performance (show for highest concurrency level)
        if all_results:
            highest_concurrency = max(all_results.keys())
            pool_stats = all_results[highest_concurrency].get('pool_stats', {})
            
            if pool_stats:
                print(f"\nPer-Pool Performance (at {highest_concurrency} workers):")
                print(f"{'Pool':<20} {'URL':<30} {'Requests':<10} {'Avg Time(ms)':<12} {'Min(ms)':<8} {'Max(ms)':<8}")
                print("-" * 95)
                
                for pool_name in sorted(pool_stats.keys()):
                    stats = pool_stats[pool_name]
                    url = selected_urls[pool_name][0]
                    pool_type = " (DEFAULT)" if 'default' in pool_name else ""
                    display_name = f"{pool_name}{pool_type}"
                    print(f"{display_name:<20} "
                          f"{url[:28]:<30} "
                          f"{stats['count']:<10} "
                          f"{stats['avg_response_time']*1000:<12.2f} "
                          f"{stats['min_response_time']*1000:<8.2f} "
                          f"{stats['max_response_time']*1000:<8.2f}")
        
        # Find best performing configuration
        best_throughput = max(all_results.items(), key=lambda x: x[1]['requests_per_second'])
        best_latency = min(all_results.items(), key=lambda x: x[1]['avg_response_time'])
        
        print(f"\nBest Throughput: {best_throughput[1]['requests_per_second']:.2f} req/s at {best_throughput[0]} workers")
        print(f"Best Latency: {best_latency[1]['avg_response_time']*1000:.2f}ms at {best_latency[0]} workers")
    
    def save_pool_test_results(self, all_results, selected_urls):
        """Save pool test results to files"""
        
        # Save summary results
        summary_filename = "pool_benchmark_summary.csv"
        with open(summary_filename, 'w') as f:
            f.write("Workers,Requests_Per_Second,Avg_Response_Time_ms,Min_Response_Time_ms,Max_Response_Time_ms,Success_Rate,Total_Test_Duration_s\n")
            
            for workers in sorted(all_results.keys()):
                stats = all_results[workers]
                f.write(f"{workers},"
                       f"{stats['requests_per_second']:.2f},"
                       f"{stats['avg_response_time']*1000:.2f},"
                       f"{stats['min_response_time']*1000:.2f},"
                       f"{stats['max_response_time']*1000:.2f},"
                       f"{stats['success_rate']:.2f},"
                       f"{stats['total_test_duration']:.2f}\n")
        
        # Save per-pool detailed results
        pool_summary_filename = "pool_performance_summary.csv"
        with open(pool_summary_filename, 'w') as f:
            f.write("Workers,Pool,URL,Is_Default,Requests,Avg_Response_Time_ms,Min_Response_Time_ms,Max_Response_Time_ms,StdDev_ms\n")
            
            for workers in sorted(all_results.keys()):
                pool_stats = all_results[workers].get('pool_stats', {})
                for pool_name, stats in pool_stats.items():
                    url = selected_urls[pool_name][0]
                    is_default = 'Yes' if 'default' in pool_name else 'No'
                    f.write(f"{workers},"
                           f"{pool_name},"
                           f"{url},"
                           f"{is_default},"
                           f"{stats['count']},"
                           f"{stats['avg_response_time']*1000:.2f},"
                           f"{stats['min_response_time']*1000:.2f},"
                           f"{stats['max_response_time']*1000:.2f},"
                           f"{stats['stdev_response_time']*1000:.2f}\n")
        
        # Save pool configuration
        config_filename = "pool_configuration.json"
        with open(config_filename, 'w') as f:
            json.dump(selected_urls, f, indent=2)
        
        print(f"\nResults saved to:")
        print(f"  - {summary_filename}")
        print(f"  - {pool_summary_filename}")
        print(f"  - {config_filename}")

def main():
    parser = argparse.ArgumentParser(description='Pool-based parallel load testing (one URL per pool)')
    parser.add_argument('--app', type=str, required=True,
                       choices=['wordpress', 'phpmyadmin', 'moodle', 'drupal', 'joomla'],
                       help='Application name')
    parser.add_argument('--base-url', default='http://localhost:8000',
                       help='Base URL for the application (default: http://localhost:8000)')
    parser.add_argument('--requests', type=int, default=15000,
                       help='Total requests per parallel level (default: 15000)')
    parser.add_argument('--parallel-levels', nargs='+', type=int, default=[1, 2, 4, 8, 16, 32],
                       help='Parallel levels to test (default: 1 2 4 8 16 32)')
    parser.add_argument('--nginx-config-dir', default='nginx-url-map-files',
                       help='Directory containing nginx URL map files')
    
    args = parser.parse_args()
    
    # Initialize benchmark
    benchmark = PoolBenchmark(base_url=args.base_url)
    
    # Get all pools including the default pool
    pools = benchmark.get_all_pools_including_default(args.nginx_config_dir, args.app)
    
    if not pools:
        print("No pools found! Make sure you've run the mpool configuration first.")
        sys.exit(1)
    
    print(f"Found {len(pools)} pools:")
    for pool_name, urls in pools.items():
        pool_type = " (DEFAULT)" if 'default' in pool_name else ""
        print(f"  {pool_name}{pool_type}: {len(urls)} URLs")
    
    # Select one popular URL from each pool
    selected_urls = benchmark.select_one_url_per_pool(pools, args.app)
    
    # Run the benchmark
    results = benchmark.run_pool_benchmark(
        selected_urls=selected_urls,
        total_requests=args.requests,
        parallel_levels=args.parallel_levels
    )

if __name__ == "__main__":
    main()