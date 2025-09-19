"""
URL Response Tester
Tests URLs and captures their responses for template migration verification
"""

from django.core.management.base import BaseCommand
from django.test import Client
from django.urls import get_resolver
import json
import os
from datetime import datetime


class Command(BaseCommand):
    help = 'Test URLs and capture responses for template migration verification'

    def add_arguments(self, parser):
        parser.add_argument(
            '--save-responses',
            action='store_true',
            help='Save HTML responses to files'
        )
        parser.add_argument(
            '--urls',
            nargs='+',
            help='Specific URLs to test'
        )

    def handle(self, *args, **options):
        self.client = Client()
        
        if options.get('urls'):
            urls_to_test = [{'url': url, 'name': f'manual_{i}'} 
                           for i, url in enumerate(options['urls'])]
        else:
            urls_to_test = self.get_common_urls()
        
        results = []
        
        for url_info in urls_to_test:
            result = self.test_url(url_info)
            results.append(result)
            
            if options.get('save_responses') and result['status_code'] == 200:
                self.save_response(result)
        
        self.print_summary(results)

    def get_common_urls(self):
        """Get list of common URLs to test"""
        return [
            {'url': '/', 'name': 'home'},
            {'url': '/accounts/login/', 'name': 'login'},
            {'url': '/accounts/register/', 'name': 'register'},
            {'url': '/accounts/password_reset/', 'name': 'password_reset'},
            {'url': '/admin/', 'name': 'admin'},
            {'url': '/patients/', 'name': 'patients_list'},
        ]

    def test_url(self, url_info):
        """Test a single URL and return result"""
        url = url_info['url']
        name = url_info.get('name', 'unknown')
        
        try:
            response = self.client.get(url, follow=True)
            
            result = {
                'url': url,
                'name': name,
                'status_code': response.status_code,
                'content_type': response.get('Content-Type', ''),
                'content_length': len(response.content),
                'template_names': getattr(response, 'template_name', []),
                'context_keys': list(response.context.keys()) if response.context else [],
                'timestamp': datetime.now().isoformat(),
                'success': response.status_code == 200,
                'content': response.content.decode('utf-8') if response.status_code == 200 else None
            }
            
            # Check for template errors in content
            if response.status_code == 200:
                content = response.content.decode('utf-8')
                if 'TemplateSyntaxError' in content:
                    result['template_error'] = True
                    result['success'] = False
                else:
                    result['template_error'] = False
            
            status_icon = '✓' if result['success'] else '✗'
            self.stdout.write(f'{status_icon} {url} ({response.status_code})')
            
            if result.get('template_error'):
                self.stdout.write(self.style.ERROR(f'  Template syntax error detected'))
            
            return result
            
        except Exception as e:
            result = {
                'url': url,
                'name': name,
                'status_code': None,
                'error': str(e),
                'success': False,
                'timestamp': datetime.now().isoformat()
            }
            
            self.stdout.write(self.style.ERROR(f'✗ {url} - Error: {e}'))
            return result

    def save_response(self, result):
        """Save HTML response to file"""
        if not result.get('content'):
            return
        
        # Create output directory
        output_dir = os.path.join('template_migration', 'responses')
        os.makedirs(output_dir, exist_ok=True)
        
        # Create filename
        filename = f"{result['name']}_{result['status_code']}.html"
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(result['content'])
        
        self.stdout.write(f'  Saved response to: {filepath}')

    def print_summary(self, results):
        """Print test summary"""
        total = len(results)
        successful = len([r for r in results if r['success']])
        template_errors = len([r for r in results if r.get('template_error')])
        
        self.stdout.write(f'\n=== SUMMARY ===')
        self.stdout.write(f'Total URLs tested: {total}')
        self.stdout.write(f'Successful: {successful}')
        self.stdout.write(f'Failed: {total - successful}')
        
        if template_errors > 0:
            self.stdout.write(
                self.style.WARNING(f'Template errors: {template_errors}')
            )
        
        # Show failed URLs
        failed = [r for r in results if not r['success']]
        if failed:
            self.stdout.write(f'\nFailed URLs:')
            for result in failed:
                error_msg = result.get('error', f"HTTP {result.get('status_code')}")
                self.stdout.write(f'  {result["url"]}: {error_msg}')
        
        # Save results to JSON
        results_file = 'template_migration/url_test_results.json'
        os.makedirs(os.path.dirname(results_file), exist_ok=True)
        
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        self.stdout.write(f'\nResults saved to: {results_file}')
