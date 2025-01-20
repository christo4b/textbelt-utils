#!/usr/bin/env python3
import os
import asyncio
import argparse
from getpass import getpass

from textbelt_utils import AsyncTextbeltClient, OTPGenerateRequest, OTPVerifyRequest

async def test_otp(phone: str = None, api_key: str = None):
    """Test the OTP functionality with interactive verification."""
    
    # Get credentials from environment or prompt
    api_key = api_key or os.getenv("TEXTBELT_API_KEY") or getpass("Enter your Textbelt API key: ")
    phone = phone or os.getenv("TEXTBELT_TEST_PHONE") or input("Enter phone number (E.164 format, e.g., +1234567890): ")

    print("\n🔐 Testing OTP functionality...")
    
    async with AsyncTextbeltClient(api_key=api_key) as client:
        # Generate and send OTP
        print("\n📤 Generating and sending OTP...")
        generate_request = OTPGenerateRequest(
            phone=phone,
            userid=phone,  # Using phone as userid for testing
            key=api_key,
            message="Your textbelt-utils test verification code is $OTP",
            lifetime=180,  # 3 minutes
            length=6
        )
        
        try:
            response = await client.generate_otp(generate_request)
            print(f"✅ OTP sent successfully!")
            print(f"📱 Message ID: {response.text_id}")
            print(f"💫 Remaining quota: {response.quota_remaining}")
            
            if response.otp:  # Only shown in test mode
                print(f"🔑 Test mode OTP: {response.otp}")
            
            # Wait for user to enter the code
            print("\n⌛ Waiting for OTP...")
            otp = input("Enter the verification code you received (or Ctrl+C to cancel): ").strip()
            
            # Verify the OTP
            print("\n🔍 Verifying OTP...")
            verify_request = OTPVerifyRequest(
                otp=otp,
                userid=phone,  # Same userid used in generate
                key=api_key
            )
            
            verify_response = await client.verify_otp(verify_request)
            
            if verify_response.is_valid_otp:
                print("✅ OTP verified successfully!")
            else:
                print("❌ Invalid OTP")
                
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return 1
    
    return 0

def main():
    parser = argparse.ArgumentParser(description="Test Textbelt OTP functionality")
    parser.add_argument("--phone", help="Phone number in E.164 format (e.g., +1234567890)")
    parser.add_argument("--key", help="Textbelt API key")
    args = parser.parse_args()
    
    try:
        return asyncio.run(test_otp(args.phone, args.key))
    except KeyboardInterrupt:
        print("\n\n🛑 Test cancelled by user")
        return 1

if __name__ == "__main__":
    exit(main()) 