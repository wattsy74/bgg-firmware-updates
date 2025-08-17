"""
X-Input Controller Testing Script
Automated testing tool for BumbleGum X-Input implementation
"""

import subprocess
import time
import json
from pathlib import Path

class XInputTester:
    def __init__(self):
        self.test_results = {}
        self.controller_detected = False
        
    def check_device_manager(self):
        """Check if Xbox controller is detected in Device Manager"""
        print("🔍 Checking Device Manager for Xbox controller...")
        
        try:
            # Use PowerShell to query device manager
            result = subprocess.run([
                'powershell', 
                'Get-PnpDevice | Where-Object {$_.FriendlyName -like "*Xbox*"} | Select-Object FriendlyName, Status'
            ], capture_output=True, text=True)
            
            if "Xbox" in result.stdout:
                print("✅ Xbox controller detected in Device Manager")
                self.controller_detected = True
                return True
            else:
                print("❌ Xbox controller NOT detected in Device Manager")
                return False
                
        except Exception as e:
            print(f"❌ Error checking Device Manager: {e}")
            return False
    
    def check_usb_devices(self):
        """Check USB VID/PID for Xbox controller"""
        print("🔍 Checking USB VID/PID...")
        
        try:
            result = subprocess.run([
                'powershell',
                'Get-PnpDevice | Where-Object {$_.InstanceId -like "*VID_045E&PID_028E*"} | Select-Object FriendlyName, Status'
            ], capture_output=True, text=True)
            
            if "VID_045E&PID_028E" in result.stdout or "Xbox" in result.stdout:
                print("✅ Correct USB VID/PID detected (045E:028E)")
                return True
            else:
                print("❌ Xbox controller USB ID not found")
                return False
                
        except Exception as e:
            print(f"❌ Error checking USB devices: {e}")
            return False
    
    def test_game_controller_panel(self):
        """Open Windows Game Controller panel for manual testing"""
        print("🎮 Opening Windows Game Controller panel...")
        print("   Please manually test all buttons and analog inputs")
        
        try:
            # Open game controller settings
            subprocess.run(['control', 'joy.cpl'], check=True)
            
            input("   Press Enter when you've finished testing in the Game Controller panel...")
            return True
            
        except Exception as e:
            print(f"❌ Error opening Game Controller panel: {e}")
            return False
    
    def check_steam_detection(self):
        """Check if Steam can detect the controller"""
        print("🎮 Checking Steam controller detection...")
        print("   Note: This requires Steam to be installed and running")
        
        # Check if Steam is running
        try:
            result = subprocess.run([
                'tasklist', '/FI', 'IMAGENAME eq steam.exe'
            ], capture_output=True, text=True)
            
            if "steam.exe" in result.stdout:
                print("✅ Steam is running")
                print("   Check Steam > Settings > Controller > General Controller Settings")
                print("   Your controller should appear as 'Xbox 360 Controller'")
                return True
            else:
                print("⚠️  Steam is not running - cannot test Steam detection")
                return False
                
        except Exception as e:
            print(f"❌ Error checking Steam: {e}")
            return False
    
    def verify_config_file(self):
        """Verify the controller is configured for X-Input mode"""
        print("🔧 Verifying configuration file...")
        
        try:
            # Check if we can find a config.json file
            config_paths = [
                "config.json",
                "../config.json", 
                "../../config.json"
            ]
            
            config_found = False
            for path in config_paths:
                if Path(path).exists():
                    with open(path, 'r') as f:
                        config = json.load(f)
                    
                    mode = config.get('controller_mode', 'not_set')
                    if mode == 'xinput':
                        print(f"✅ Config file found with X-Input mode enabled: {path}")
                        config_found = True
                        break
                    else:
                        print(f"⚠️  Config file found but mode is '{mode}': {path}")
            
            if not config_found:
                print("❌ No config.json file found with X-Input mode")
                return False
                
            return True
            
        except Exception as e:
            print(f"❌ Error checking config file: {e}")
            return False
    
    def run_basic_tests(self):
        """Run basic automated tests"""
        print("🚀 Starting X-Input Basic Tests")
        print("=" * 50)
        
        tests = [
            ("Config File Check", self.verify_config_file),
            ("Device Manager Check", self.check_device_manager),
            ("USB VID/PID Check", self.check_usb_devices),
            ("Steam Detection", self.check_steam_detection),
        ]
        
        results = {}
        for test_name, test_func in tests:
            print(f"\n🧪 Running: {test_name}")
            try:
                results[test_name] = test_func()
            except Exception as e:
                print(f"❌ Test failed with exception: {e}")
                results[test_name] = False
        
        return results
    
    def run_manual_tests(self):
        """Guide through manual testing steps"""
        print("\n🎯 Manual Testing Required")
        print("=" * 50)
        
        manual_tests = [
            {
                "name": "Game Controller Panel",
                "description": "Test all buttons and analog inputs",
                "action": self.test_game_controller_panel
            },
            {
                "name": "Game Testing", 
                "description": "Test with a game like Rocket League",
                "action": lambda: self.manual_game_test()
            }
        ]
        
        for test in manual_tests:
            print(f"\n🧪 Manual Test: {test['name']}")
            print(f"   {test['description']}")
            
            if input("   Run this test? (y/n): ").lower() == 'y':
                test['action']()
    
    def manual_game_test(self):
        """Guide through manual game testing"""
        print("🎮 Manual Game Testing Guide:")
        print("   1. Launch a game that supports Xbox controllers (e.g., Rocket League)")
        print("   2. Go to controller settings in the game")
        print("   3. Verify it detects as 'Xbox 360 Controller'")
        print("   4. Test all guitar buttons map to correct game functions")
        print("   5. Test whammy bar works as trigger/analog input")
        
        input("   Press Enter when you've finished game testing...")
    
    def generate_report(self, results):
        """Generate a test report"""
        print("\n📊 X-Input Test Report")
        print("=" * 50)
        
        passed = sum(1 for r in results.values() if r)
        total = len(results)
        
        print(f"Tests Passed: {passed}/{total}")
        print()
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"  {status} - {test_name}")
        
        if passed == total:
            print("\n🎉 All tests passed! X-Input implementation is working correctly.")
        else:
            print(f"\n⚠️  {total - passed} test(s) failed. Review the issues above.")
        
        # Save report to file
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        report_file = f"xinput_test_report_{timestamp}.txt"
        
        with open(report_file, 'w') as f:
            f.write("X-Input Test Report\n")
            f.write("=" * 30 + "\n")
            f.write(f"Date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Tests Passed: {passed}/{total}\n\n")
            
            for test_name, result in results.items():
                status = "PASS" if result else "FAIL"
                f.write(f"{status} - {test_name}\n")
        
        print(f"\n📄 Report saved to: {report_file}")

def main():
    print("🎸 BumbleGum X-Input Testing Tool")
    print("=" * 50)
    print("This tool will help test your X-Input firmware implementation")
    print()
    
    tester = XInputTester()
    
    # Run automated tests
    results = tester.run_basic_tests()
    
    # Ask about manual tests
    if input("\nRun manual tests? (y/n): ").lower() == 'y':
        tester.run_manual_tests()
    
    # Generate report
    tester.generate_report(results)
    
    print("\n🏁 Testing complete!")

if __name__ == "__main__":
    main()
