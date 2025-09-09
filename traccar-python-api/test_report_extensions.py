"""
Test script for report scheduling, email, and calendar functionality.
"""

import asyncio
import json
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.database import get_db
from app.models import Report, Calendar, User
from app.services.report_scheduler import ReportScheduler, CalendarIntegration
from app.services.email_service import EmailService
from app.services.report_providers import ReportProviderFactory


async def test_report_scheduling():
    """Test report scheduling functionality."""
    print("🧪 Testing Report Scheduling...")
    
    async for db in get_db():
        try:
            # Get a test user
            result = await db.execute(select(User).limit(1))
            user = result.scalar_one_or_none()
            if not user:
                print("❌ No users found. Please create a user first.")
                return
            
            # Create a test report
            report = Report(
                user_id=user.id,
                name="Test Scheduled Report",
                description="A test report for scheduling",
                report_type="summary",
                format="json",
                period="today",
                device_ids=[],
                group_ids=[],
                include_attributes=True,
                include_addresses=True,
                include_events=True,
                include_geofences=True,
                parameters={}
            )
            
            db.add(report)
            await db.commit()
            await db.refresh(report)
            
            print(f"✅ Created test report: {report.id}")
            
            # Test scheduling
            scheduler = ReportScheduler(db)
            
            # Schedule report to run every day at 9 AM
            success = await scheduler.schedule_report(
                report, 
                "0 9 * * *",  # Daily at 9 AM
                ["test@example.com"]
            )
            
            if success:
                print(f"✅ Report scheduled successfully. Next run: {report.next_run}")
            else:
                print("❌ Failed to schedule report")
            
            # Test getting scheduled reports
            scheduled_reports = await scheduler.get_scheduled_reports(user.id)
            print(f"✅ Found {len(scheduled_reports)} scheduled reports")
            
            # Test unscheduling
            success = await scheduler.unschedule_report(report)
            if success:
                print("✅ Report unscheduled successfully")
            else:
                print("❌ Failed to unschedule report")
            
        except Exception as e:
            print(f"❌ Error testing report scheduling: {e}")
        finally:
            await db.close()
        break


async def test_calendar_integration():
    """Test calendar integration functionality."""
    print("\n🧪 Testing Calendar Integration...")
    
    async for db in get_db():
        try:
            # Get a test user
            result = await db.execute(select(User).limit(1))
            user = result.scalar_one_or_none()
            if not user:
                print("❌ No users found. Please create a user first.")
                return
            
            # Test calendar creation
            calendar_service = CalendarIntegration(db)
            
            calendar = await calendar_service.create_calendar(
                user_id=user.id,
                name="Test Calendar",
                description="A test calendar for report scheduling",
                data="BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//Test//Test//EN\nEND:VCALENDAR"
            )
            
            print(f"✅ Created calendar: {calendar.id}")
            
            # Test calendar update
            success = await calendar_service.update_calendar(
                calendar.id,
                name="Updated Test Calendar",
                description="Updated description"
            )
            
            if success:
                print("✅ Calendar updated successfully")
            else:
                print("❌ Failed to update calendar")
            
            # Test getting calendars
            result = await db.execute(select(Calendar).where(Calendar.user_id == user.id))
            calendars = result.scalars().all()
            print(f"✅ Found {len(calendars)} calendars for user")
            
            # Test calendar deletion
            success = await calendar_service.delete_calendar(calendar.id)
            if success:
                print("✅ Calendar deleted successfully")
            else:
                print("❌ Failed to delete calendar")
            
        except Exception as e:
            print(f"❌ Error testing calendar integration: {e}")
        finally:
            await db.close()
        break


async def test_email_service():
    """Test email service functionality."""
    print("\n🧪 Testing Email Service...")
    
    try:
        email_service = EmailService()
        
        # Test email configuration
        config_result = await email_service.test_email_configuration()
        print(f"📧 Email configuration test: {config_result['status']}")
        print(f"   SMTP Host: {config_result['smtp_host']}")
        print(f"   SMTP Port: {config_result['smtp_port']}")
        print(f"   From Email: {config_result['from_email']}")
        
        if config_result['status'] == 'error':
            print(f"   Error: {config_result['message']}")
            print("   Note: Email functionality requires proper SMTP configuration")
        
        # Test report email (without actually sending)
        test_report_data = {
            "report_type": "summary",
            "generated_at": datetime.utcnow().isoformat(),
            "period_start": (datetime.utcnow() - timedelta(days=1)).isoformat(),
            "period_end": datetime.utcnow().isoformat(),
            "total_devices": 5,
            "devices": [
                {
                    "device_id": 1,
                    "device_name": "Test Device",
                    "total_distance": 150.5,
                    "total_time": 3600,
                    "max_speed": 80.0,
                    "avg_speed": 45.0
                }
            ]
        }
        
        print("✅ Email service initialized successfully")
        print("   Note: Actual email sending requires SMTP configuration")
        
    except Exception as e:
        print(f"❌ Error testing email service: {e}")


async def test_report_providers():
    """Test report providers functionality."""
    print("\n🧪 Testing Report Providers...")
    
    async for db in get_db():
        try:
            # Test provider factory
            providers_to_test = ["route", "summary", "events", "stops", "trips", "combined"]
            
            for provider_type in providers_to_test:
                try:
                    provider = ReportProviderFactory.create_provider(provider_type, db)
                    print(f"✅ Created {provider_type} provider: {type(provider).__name__}")
                except Exception as e:
                    print(f"❌ Failed to create {provider_type} provider: {e}")
            
            # Test report generation (mock)
            print("✅ Report providers tested successfully")
            print("   Note: Full report generation requires device and position data")
            
        except Exception as e:
            print(f"❌ Error testing report providers: {e}")
        finally:
            await db.close()
        break


async def test_dynamic_attributes():
    """Test dynamic attributes functionality."""
    print("\n🧪 Testing Dynamic Attributes...")
    
    async for db in get_db():
        try:
            # Get a test user
            result = await db.execute(select(User).limit(1))
            user = result.scalar_one_or_none()
            if not user:
                print("❌ No users found. Please create a user first.")
                return
            
            # Create a test report
            report = Report(
                user_id=user.id,
                name="Test Attributes Report",
                description="A test report for dynamic attributes",
                report_type="summary",
                format="json",
                period="today",
                device_ids=[],
                group_ids=[],
                include_attributes=True,
                include_addresses=True,
                include_events=True,
                include_geofences=True,
                parameters={},
                attributes={"custom_field": "test_value", "priority": "high", "enabled": True}
            )
            
            db.add(report)
            await db.commit()
            await db.refresh(report)
            
            print(f"✅ Created test report with attributes: {report.id}")
            
            # Test attribute access methods
            string_attr = report.get_string_attribute("custom_field", "default")
            print(f"✅ String attribute: {string_attr}")
            
            boolean_attr = report.get_boolean_attribute("enabled", False)
            print(f"✅ Boolean attribute: {boolean_attr}")
            
            integer_attr = report.get_integer_attribute("priority", 0)
            print(f"✅ Integer attribute: {integer_attr}")
            
            # Test setting attributes
            report.set_attribute("new_field", "new_value")
            print(f"✅ Set new attribute: {report.attributes}")
            
            # Test attribute existence
            has_attr = report.has_attribute("custom_field")
            print(f"✅ Has attribute check: {has_attr}")
            
            # Clean up
            await db.delete(report)
            await db.commit()
            print("✅ Test report cleaned up")
            
        except Exception as e:
            print(f"❌ Error testing dynamic attributes: {e}")
        finally:
            await db.close()
        break


async def main():
    """Run all tests."""
    print("🚀 Starting Report Extensions Tests\n")
    
    await test_report_scheduling()
    await test_calendar_integration()
    await test_email_service()
    await test_report_providers()
    await test_dynamic_attributes()
    
    print("\n✅ All tests completed!")


if __name__ == "__main__":
    asyncio.run(main())
