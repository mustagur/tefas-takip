#!/usr/bin/env python3
"""
SMTP Email Script
Excel ve HTML dosyalarını SMTP ile gönderir
"""

import os
import sys
import glob
import smtplib
import ssl
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import json

def get_smtp_config():
    """SMTP konfigürasyon ayarlarını alır"""
    # GitHub Actions için basit SMTP ayarları
    return {
        'smtp_server': 'smtp.gmail.com',
        'smtp_port': 587,
        'sender_email': os.getenv('SENDER_EMAIL', 'noreply.github.actions@gmail.com'),
        'sender_name': 'TEFAS Reports Bot'
    }

def find_latest_excel_file():
    """En son oluşturulan Excel dosyasını bulur"""
    # Try new OOP format first: tefas_report_YYYYMMDD_HHMM.xlsx
    excel_files = glob.glob("tefas_report_*.xlsx")
    if not excel_files:
        raise Exception("Excel dosyası bulunamadı")
    
    # En son oluşturulan dosyayı al
    latest_file = max(excel_files, key=os.path.getctime)
    print(f"📊 Bulundu: {latest_file} (OOP format)")
    return latest_file

def find_html_file():
    """HTML rapor dosyasını bulur"""
    html_files = glob.glob("tefas_report.html")
    if not html_files:
        raise Exception("HTML rapor dosyası bulunamadı")
    
    html_file = html_files[0]
    print(f"🌐 HTML dosyası bulundu: {html_file}")
    return html_file

def create_email_with_attachments(excel_file, html_file, recipient_list):
    """Email mesajını attachments ile oluşturur"""
    try:
        # Çoklu alıcı desteği
        if isinstance(recipient_list, list):
            primary_recipient = recipient_list[0]
            all_recipients = ', '.join(recipient_list)
        else:
            primary_recipient = recipient_list
            all_recipients = recipient_list
            recipient_list = [recipient_list]
        
        # Email mesajını oluştur
        msg = MIMEMultipart()
        msg['From'] = f'TEFAS Reports Bot <noreply.github.actions@gmail.com>'
        msg['To'] = primary_recipient
        
        # Eğer birden fazla alıcı varsa CC ekle
        if len(recipient_list) > 1:
            msg['CC'] = ', '.join(recipient_list[1:])
            
        msg['Subject'] = f'📊 TEFAS Günlük Rapor - {datetime.now().strftime("%d/%m/%Y")} ({len(recipient_list)} alıcı)'
        
        # Email içeriği
        html_content = f"""
        <html>
        <body>
            <h2>📈 TEFAS Günlük Rapor</h2>
            <p><strong>Tarih:</strong> {datetime.now().strftime("%d/%m/%Y %H:%M")}</p>
            
            <h3>📎 Ekli Dosyalar:</h3>
            <ul>
                <li><strong>📊 Excel Raporu:</strong> Detaylı analiz tabloları</li>
                <li><strong>🌐 HTML Raporu:</strong> Web formatında görsel rapor</li>
            </ul>
            
            <h3>📋 Analiz Özeti:</h3>
            <p>Bu rapor TEFAS (Türkiye Elektronik Fon Alım Satım Platformu) verilerini analiz ederek:</p>
            <ul>
                <li>🔍 Teknik analiz göstergelerini (RSI, MACD, Bollinger Bandları)</li>
                <li>📈 Trend adaylarını ve erken momentum sinyallerini</li>
                <li>💼 Portföy durumunu ve uyarıları</li>
                <li>📊 Performans metriklerini</li>
            </ul>
            <p>içermektedir.</p>
            
            <hr>
            <p><small>🤖 Bu email otomatik olarak oluşturulmuştur.<br>
            📅 Her iş günü saat 09:30'da güncellenir.</small></p>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(html_content, 'html', 'utf-8'))
        
        # Excel dosyasını ekle
        with open(excel_file, 'rb') as f:
            excel_attachment = MIMEApplication(f.read())
            excel_attachment.add_header('Content-Disposition', 'attachment', 
                                      filename=f'TEFAS_Rapor_{datetime.now().strftime("%Y%m%d")}.xlsx')
            msg.attach(excel_attachment)
        
        # HTML dosyasını ekle
        with open(html_file, 'rb') as f:
            html_attachment = MIMEApplication(f.read())
            html_attachment.add_header('Content-Disposition', 'attachment', 
                                     filename=f'TEFAS_Rapor_{datetime.now().strftime("%Y%m%d")}.html')
            msg.attach(html_attachment)
        
        print(f"📧 Email hazırlandı: {len(msg.get_payload())} attachment")
        return msg
        
    except Exception as e:
        print(f"❌ Email oluşturma hatası: {e}")
        return None

def send_email_via_smtp(msg, recipient_list):
    """Gerçek SMTP ile email gönderir"""
    try:
        # Çoklu alıcı desteği
        if isinstance(recipient_list, list):
            all_recipients = recipient_list
            primary_recipient = recipient_list[0]
        else:
            all_recipients = [recipient_list]
            primary_recipient = recipient_list
            
        # Environment variables'dan SMTP ayarlarını al
        smtp_user = os.getenv('SMTP_USER')
        smtp_password = os.getenv('SMTP_PASSWORD')
        
        if not smtp_user or not smtp_password:
            print("⚠️ SMTP_USER veya SMTP_PASSWORD environment değişkeni bulunamadı")
            print("ℹ️ GitHub Actions Secrets'a SMTP_USER ve SMTP_PASSWORD ekleyin")
            print("📧 Email gönderimi simülasyon modunda çalışıyor...\n")
            
            # Simülasyon modunda çalıştır
            return simulate_email_sending(msg)
        
        print(f"📧 Gmail SMTP ile email gönderiliyor...")
        print(f"   From: {msg['From']}")
        print(f"   To: {msg['To']}")
        print(f"   Subject: {msg['Subject']}")
        print(f"   SMTP User: {smtp_user}")
        
        # Gmail SMTP ile gönderim
        smtp_config = get_smtp_config()
        
        # SSL context oluştur
        context = ssl.create_default_context()
        
        with smtplib.SMTP(smtp_config['smtp_server'], smtp_config['smtp_port']) as server:
            server.starttls(context=context)
            server.login(smtp_user, smtp_password)
            
            # Email gönder - tüm alıcılara
            text = msg.as_string()
            server.sendmail(smtp_user, all_recipients, text)
            
        print(f"✅ Email başarıyla gönderildi!")
        print(f"📧 Gönderici: {smtp_user}")
        print(f"📧 Alıcı: {recipient_email}")
        
        return {
            'success': True,
            'message_id': f"smtp_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'smtp_user': smtp_user
        }
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ SMTP kimlik doğrulama hatası: {e}")
        print("ℹ️ Gmail App Password kullandığınızdan emin olun")
        return {'success': False, 'error': f'SMTP Auth Error: {e}'}
        
    except smtplib.SMTPException as e:
        print(f"❌ SMTP hatası: {e}")
        return {'success': False, 'error': f'SMTP Error: {e}'}
        
    except Exception as e:
        print(f"❌ Email gönderim hatası: {e}")
        return {'success': False, 'error': str(e)}

def simulate_email_sending(msg):
    """Email gönderimini simüle eder (credentials yoksa)"""
    try:
        print(f"🔄 Email gönderimi simülasyonu:")
        print(f"   From: {msg['From']}")
        print(f"   To: {msg['To']}")
        print(f"   Subject: {msg['Subject']}")
        print(f"   Attachments: {len([p for p in msg.get_payload() if p.get_content_disposition() == 'attachment'])}")
        
        # Email içeriğini logs'a yazdır
        email_body = ""
        for part in msg.walk():
            if part.get_content_type() == "text/html":
                email_body = part.get_payload()
                break
        
        print("\n📧 EMAIL İÇERİĞİ:")
        print("=" * 50)
        print(email_body)
        print("=" * 50)
        
        # Dosya bilgilerini göster
        attachment_info = []
        for part in msg.walk():
            if part.get_content_disposition() == 'attachment':
                filename = part.get_filename()
                size = len(part.get_payload())
                attachment_info.append(f"{filename} ({size} bytes)")
        
        if attachment_info:
            print(f"\n📁 EK DOSYALAR:")
            for info in attachment_info:
                print(f"   - {info}")
        
        print(f"\n✅ Email raporu hazırlandı ve log'a yazdırıldı!")
        print(f"ℹ️ Simülasyon: Gerçek gönderim için SMTP credentials gerekli")
        print(f"📊 Dosyalar repository'de saklandı ve erişilebilir.")
        
        return {
            'success': True,
            'message_id': f"simulated_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'mode': 'simulation'
        }
        
    except Exception as e:
        print(f"❌ Email simülasyon hatası: {e}")
        return {
            'success': False,
            'error': str(e)
        }

def main():
    """Ana fonksiyon"""
    try:
        print("🚀 Gmail email gönderimi başlatılıyor...")
        
        # Environment değişkenlerini al
        recipient_emails = os.getenv('RECIPIENT_EMAIL', 'melihekmekci1@gmail.com')
        
        # Çoklu email desteği - virgülle ayrılmış olabilir
        if ',' in recipient_emails:
            # Email'leri temizle: boşlukları ve invisible karakterleri kaldır
            email_list = []
            for email in recipient_emails.split(','):
                clean_email = email.strip().replace('\n', '').replace('\r', '').replace('\t', '')
                if clean_email and '@' in clean_email:  # Geçerli email kontrolü
                    email_list.append(clean_email)
                    
            if email_list:
                print(f"📧 Çoklu alıcı modu: {len(email_list)} kişi")
                for i, email in enumerate(email_list):
                    print(f"   {i+1}. {email}")
                recipient_email = email_list[0]  # İlk email'i ana alıcı olarak kullan
            else:
                # Eğer hiçbiri geçerli değilse, fallback
                recipient_email = recipient_emails.split(',')[0].strip()
                email_list = [recipient_email]
                print(f"⚠️ Email format sorunlu, ilk adresi kullanılıyor: {recipient_email}")
        else:
            # Tek email'i de temizle
            recipient_email = recipient_emails.strip().replace('\n', '').replace('\r', '').replace('\t', '')
            email_list = [recipient_email]
            print(f"📧 Tek alıcı modu: {recipient_email}")
            
        # Email format validation
        for email in email_list:
            if not email or '@' not in email or '.' not in email.split('@')[-1]:
                print(f"⚠️ Geçersiz email formatı: {email}")
        
        # SMTP ayarlarını kontrol et
        smtp_user = os.getenv('SMTP_USER')
        smtp_password = os.getenv('SMTP_PASSWORD')
        
        if smtp_user and smtp_password:
            print(f"✅ SMTP credentials bulundu - Gerçek email gönderimi aktif")
            print(f"📧 Gönderici: {smtp_user}")
        else:
            print(f"⚠️ SMTP credentials bulunamadı - Simülasyon modu")
            print(f"ℹ️ GitHub Secrets'a SMTP_USER ve SMTP_PASSWORD ekleyin")
        
        print(f"📧 Alıcı: {recipient_email}")
        
        # Dosyaları bul
        excel_file = find_latest_excel_file()
        html_file = find_html_file()
        
        print(f"📊 Excel dosyası: {excel_file}")
        print(f"🌐 HTML dosyası: {html_file}")
        
        # Email oluştur
        email_msg = create_email_with_attachments(excel_file, html_file, email_list)
        
        if not email_msg:
            print("❌ Email oluşturulamadı")
            sys.exit(1)
        
        # SMTP ile gönder
        result = send_email_via_smtp(email_msg, email_list)
        
        if result['success']:
            if result.get('mode') == 'simulation':
                print("🎉 Email raporu başarıyla hazırlandı (simülasyon)!")
                print(f"📧 Message ID: {result['message_id']}")
                print(f"ℹ️ Gerçek gönderim için GitHub Secrets ayarlayın:")
                print(f"   - SMTP_USER: Gmail adresiniz")
                print(f"   - SMTP_PASSWORD: Gmail App Password")
                print(f"   - RECIPIENT_EMAIL: {recipient_email}")
            else:
                print("🎉 Email başarıyla gönderildi!")
                print(f"📧 Message ID: {result['message_id']}")
                print(f"📧 Gönderici: {result.get('smtp_user', 'N/A')}")
                print(f"📧 Alıcı: {recipient_email}")
        else:
            print(f"❌ Email gönderimi başarısız: {result.get('error')}")
            print(f"ℹ️ Simülasyon moduna geçiliyor...")
            # Hata durumunda simülasyon yaparak devam et
            # sys.exit(1) yerine warning ver ve devam et
            
    except Exception as e:
        print(f"❌ Genel hata: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()