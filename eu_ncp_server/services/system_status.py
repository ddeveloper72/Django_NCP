"""
System Status Service
Provides real-time status checking for EU eHealth NCP infrastructure components
"""

from datetime import datetime, timezone
from typing import Dict, Any
import requests
from django.conf import settings
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)


class SystemStatusService:
    """Service for checking and caching system component status"""
    
    CACHE_KEY = "system_status"
    CACHE_TIMEOUT = 300  # 5 minutes
    
    @classmethod
    def get_system_status(cls) -> Dict[str, Any]:
        """
        Get current system status with caching
        Returns cached status if available, otherwise performs fresh check
        """
        cached_status = cache.get(cls.CACHE_KEY)
        if cached_status:
            return cached_status
        
        return cls.check_system_status()
    
    @classmethod
    def check_system_status(cls) -> Dict[str, Any]:
        """
        Perform real-time system status check
        Returns status information for all components
        """
        status = {
            'last_updated': datetime.now(timezone.utc),
            'overall_status': 'operational',
            'components': {
                'api_gateway': cls._check_api_gateway(),
                'smp_services': cls._check_smp_services(),
                'authentication': cls._check_authentication(),
            }
        }
        
        # Determine overall status based on components
        component_statuses = [comp['status'] for comp in status['components'].values()]
        if 'offline' in component_statuses:
            status['overall_status'] = 'degraded'
        elif 'warning' in component_statuses:
            status['overall_status'] = 'warning'
        
        # Cache the status
        cache.set(cls.CACHE_KEY, status, cls.CACHE_TIMEOUT)
        
        return status
    
    @classmethod
    def _check_api_gateway(cls) -> Dict[str, Any]:
        """Check API Gateway status"""
        try:
            # Test a simple API endpoint
            response = requests.get(
                'http://127.0.0.1:8000/api/countries/',
                timeout=5,
                headers={'Accept': 'application/json'}
            )
            
            if response.status_code in [200, 403]:  # 403 is expected for unauthenticated requests
                return {
                    'status': 'online',
                    'label': 'Online',
                    'last_check': datetime.now(timezone.utc),
                    'response_time': response.elapsed.total_seconds() * 1000  # ms
                }
            else:
                return {
                    'status': 'warning',
                    'label': 'Issues',
                    'last_check': datetime.now(timezone.utc),
                    'error': f'HTTP {response.status_code}'
                }
                
        except requests.RequestException as e:
            logger.error(f"API Gateway check failed: {e}")
            return {
                'status': 'offline',
                'label': 'Offline',
                'last_check': datetime.now(timezone.utc),
                'error': str(e)
            }
    
    @classmethod
    def _check_smp_services(cls) -> Dict[str, Any]:
        """Check SMP Services status"""
        try:
            # Import here to avoid circular imports
            from smp_client.models import SMPConfiguration
            
            # Check if SMP configuration exists and is enabled
            smp_config = SMPConfiguration.objects.first()
            
            if smp_config and smp_config.sync_enabled:
                # Could add actual SMP endpoint check here
                return {
                    'status': 'online',
                    'label': 'Active',
                    'last_check': datetime.now(timezone.utc),
                    'config': 'European SMP'
                }
            else:
                return {
                    'status': 'warning',
                    'label': 'Disabled',
                    'last_check': datetime.now(timezone.utc),
                    'note': 'SMP sync disabled'
                }
                
        except Exception as e:
            logger.error(f"SMP Services check failed: {e}")
            return {
                'status': 'offline',
                'label': 'Error',
                'last_check': datetime.now(timezone.utc),
                'error': str(e)
            }
    
    @classmethod
    def _check_authentication(cls) -> Dict[str, Any]:
        """Check Authentication system status"""
        try:
            # Import here to avoid circular imports
            from django.contrib.auth.models import User
            
            # Simple check - can we query users?
            user_count = User.objects.count()
            
            return {
                'status': 'online',
                'label': 'Enabled',
                'last_check': datetime.now(timezone.utc),
                'users': user_count
            }
            
        except Exception as e:
            logger.error(f"Authentication check failed: {e}")
            return {
                'status': 'offline',
                'label': 'Error',
                'last_check': datetime.now(timezone.utc),
                'error': str(e)
            }
    
    @classmethod
    def force_status_refresh(cls) -> Dict[str, Any]:
        """Force a fresh status check, bypassing cache"""
        cache.delete(cls.CACHE_KEY)
        return cls.check_system_status()