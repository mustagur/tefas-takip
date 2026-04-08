#!/usr/bin/env python3
"""
Quick Email Test Script
Gmail SMTP ayarlarını test etmek için
"""
import os
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def test_gmail_smtp():
    """Gmail SMTP bağlantısını test eder"""
    print("🧪 Gmail SMTP Test Başlatılıyor...\n")
    
    # Kullanıcıdan bilgileri al
    smtp_user = input("📧 Gmail adresiniz: ").strip()
    smtp_password = input("🔑 Gmail App Password (16 haneli): ").strip()
    recipient = input("📨 Test email gönderilecek adres: ").strip()
    
    print(f"\n🔧 Test ediliyor...")
    print(f"   From: {smtp_user}")
    print(f"   To: {recipient}")
    print(f"   Password: {'*' * len(smtp_password)}")
    
    try:
        # Test emaili oluştur
        msg = MIMEMultipart()
        msg['From'] = f'TEFAS Test <{smtp_user}>'
        msg['To'] = recipient
        msg['Subject'] = '🧪 TEFAS Email Test - Başarılı!'
        
        # Email içeriği
        body = f"""
        <html>
        <body>
            <h2>🎉 Gmail SMTP Test Başarılı!</h2>
            <p><strong>Tarih:</strong> {__import__('datetime').datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
            <p><strong>Gönderen:</strong> {smtp_user}</p>
            <p><strong>Alıcı:</strong> {recipient}</p>
            
            <h3>✅ Test Sonuçları:</h3>
            <ul>
                <li>Gmail App Password: Çalışıyor</li>
                <li>SMTP Bağlantısı: Başarılı</li>
                <li>Email Gönderimi: Tamamlandı</li>
            </ul>
            
            <p>🚀 <strong>TEFAS otomatik raporları artık çalışacak!</strong></p>
            
            <hr>
            <small>Bu test emailidir. TEFAS sistem kurulumu tamamlandıktan sonra silinebilir.</small>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(body, 'html', 'utf-8'))
        
        # Gmail SMTP ile gönder
        print("\n📡 Gmail SMTP'ye bağlanıyor...")
        context = ssl.create_default_context()
        
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls(context=context)
            print("🔐 Kimlik doğrulaması yapılıyor...")
            server.login(smtp_user, smtp_password)
            
            print("📤 Email gönderiliyor...")
            text = msg.as_string()
            server.sendmail(smtp_user, recipient, text)
        
        print("\n🎉 ✅ TEST BAŞARILI!")
        print("📧 Test emaili gönderildi!")
        print("📥 Şimdi email kutunuzu kontrol edin.")
        print("🚀 TEFAS sistemi çalışmaya hazır!")
        
        print("\n📋 GitHub Secrets'a eklenecek değerler:")
        print(f"SMTP_USER = {smtp_user}")
        print(f"SMTP_PASSWORD = {smtp_password}")
        print(f"RECIPIENT_EMAIL = {recipient}")
        
    except smtplib.SMTPAuthenticationError:
        print("\n❌ KİMLİK DOĞRULAMA HATASI!")
        print("🔧 Kontrol edin:")
        print("   - Gmail'de 2-Step Verification aktif mi?")
        print("   - App Password doğru mu? (16 haneli, boşluksuz)")
        print("   - Gmail adresi doğru mu?")
        print("\n💡 Yeni App Password oluşturun:")
        print("   myaccount.google.com → Security → App passwords")
        
    except smtplib.SMTPException as e:
        print(f"\n❌ SMTP HATASI: {e}")
        print("🔧 İnternet bağlantınızı kontrol edin")
        
    except Exception as e:
        print(f"\n❌ GENEL HATA: {e}")

if __name__ == "__main__":
    test_gmail_smtp()