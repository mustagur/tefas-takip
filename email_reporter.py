#!/usr/bin/env python3
"""
Email Reporter Module
Handles email sending functionality with SMTP or fallback simulation
"""

import os
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Optional
from config import config


class EmailReporter:
    """Handles email sending with SMTP support"""
    
    def __init__(self):
        self.config = config
        self.smtp_user = os.getenv('SMTP_USER', '')
        self.smtp_password = os.getenv('SMTP_PASSWORD', '')
        self.recipient_email = os.getenv('RECIPIENT_EMAIL', '')
        
    def can_send_email(self) -> bool:
        """Check if email sending is properly configured"""
        return bool(self.smtp_user and self.smtp_password and self.recipient_email)
    
    def send_report_email(
        self, 
        html_file: str, 
        early_momentum_count: int, 
        trend_candidates_count: int, 
        portfolio_alerts: int,
        stats: Optional[object] = None
    ) -> bool:
        """Send HTML report via email"""
        
        if not self.can_send_email():
            print("⚠️ Email gönderimi simüle ediliyor (SMTP bilgileri eksik)")
            self._simulate_email_send(html_file, early_momentum_count, trend_candidates_count, portfolio_alerts)
            return False
        
        try:
            # Prepare recipients
            recipients = self._parse_recipients(self.recipient_email)
            
            # Create message
            msg = self._create_email_message(
                recipients, 
                early_momentum_count, 
                trend_candidates_count, 
                portfolio_alerts,
                stats
            )
            
            # Attach HTML file
            if os.path.exists(html_file):
                with open(html_file, 'rb') as attachment:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment.read())
                
                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename= {os.path.basename(html_file)}'
                )
                msg.attach(part)
            
            # Send email
            return self._send_smtp_email(msg, recipients)
            
        except Exception as e:
            print(f"❌ Email gönderim hatası: {e}")
            print("⚠️ Simülasyon moduna geçiliyor...")
            self._simulate_email_send(html_file, early_momentum_count, trend_candidates_count, portfolio_alerts)
            return False
    
    def _parse_recipients(self, recipient_str: str) -> List[str]:
        """Parse comma-separated recipient emails"""
        return [email.strip() for email in recipient_str.split(',') if email.strip()]
    
    def _create_email_message(
        self, 
        recipients: List[str], 
        early_momentum_count: int, 
        trend_candidates_count: int, 
        portfolio_alerts: int,
        stats: Optional[object] = None
    ) -> MIMEMultipart:
        """Create email message with proper headers and body"""
        
        msg = MIMEMultipart()
        msg['From'] = self.smtp_user
        msg['To'] = ', '.join(recipients)
        msg['Subject'] = self._generate_email_subject(
            early_momentum_count, trend_candidates_count, portfolio_alerts
        )
        
        # Email body
        body = self._generate_email_body(
            early_momentum_count, trend_candidates_count, portfolio_alerts, stats
        )
        
        msg.attach(MIMEText(body, 'html', 'utf-8'))
        return msg
    
    def _generate_email_subject(
        self, 
        early_momentum_count: int, 
        trend_candidates_count: int, 
        portfolio_alerts: int
    ) -> str:
        """Generate dynamic email subject"""
        
        today = datetime.now().strftime('%d/%m/%Y')
        alert_str = f" ⚠️ {portfolio_alerts} Uyarı" if portfolio_alerts > 0 else ""
        
        return f"TEFAS Günlük Rapor {today} - {early_momentum_count + trend_candidates_count} Aday{alert_str}"
    
    def _generate_email_body(
        self, 
        early_momentum_count: int, 
        trend_candidates_count: int, 
        portfolio_alerts: int,
        stats: Optional[object] = None
    ) -> str:
        """Generate HTML email body"""
        
        stats_section = ""
        if stats:
            stats_section = f"""
            <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 20px 0;">
                <h3>📊 Analiz İstatistikleri</h3>
                <ul>
                    <li><strong>Süre:</strong> {stats.elapsed_time/60:.1f} dakika</li>
                    <li><strong>Toplam Fonlar:</strong> {stats.total_funds:,}</li>
                    <li><strong>Analiz Edilen:</strong> {stats.processed_funds:,}</li>
                    <li><strong>İşlem Hızı:</strong> {stats.processing_rate:.1f} fon/saniye</li>
                </ul>
            </div>
"""
        
        return f"""
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TEFAS Günlük Rapor</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 20px; background: #f5f5f7; }}
        .container {{ max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.15); }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 25px; border-radius: 8px; text-align: center; margin-bottom: 25px; }}
        .summary {{ display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin: 20px 0; }}
        .summary-card {{ background: #f8f9fa; padding: 20px; border-radius: 8px; text-align: center; }}
        .summary-number {{ font-size: 2em; font-weight: bold; margin-bottom: 5px; }}
        .positive {{ color: #28a745; }}
        .negative {{ color: #dc3545; }}
        .footer {{ text-align: center; margin-top: 30px; padding: 20px; background: #f8f9fa; border-radius: 8px; color: #6c757d; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📈 TEFAS Günlük Rapor</h1>
            <p>OOP v2.0 | {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
        </div>
        
        <div class="summary">
            <div class="summary-card">
                <div class="summary-number positive">{early_momentum_count}</div>
                <div>Erken Momentum</div>
            </div>
            <div class="summary-card">
                <div class="summary-number positive">{trend_candidates_count}</div>
                <div>Güçlü Trend</div>
            </div>
        </div>
        
        {"<div class='summary-card' style='background: #f8d7da; border: 1px solid #dc3545;'><div class='summary-number negative'>" + str(portfolio_alerts) + "</div><div>Portföy Uyarısı</div></div>" if portfolio_alerts > 0 else ""}
        
        {stats_section}
        
        <div style="background: #d4edda; padding: 15px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #28a745;">
            <h3>📎 Detaylı Rapor</h3>
            <p>Ekli HTML dosyasında tüm analiz sonuçlarını, portföy durumunu ve teknik göstergeleri bulabilirsiniz.</p>
        </div>
        
        <div class="footer">
            <p>🤖 Bu email TEFAS OOP v2.0 sistemi tarafından otomatik olarak gönderilmiştir.</p>
            <p>📅 Her iş günü otomatik olarak güncellenir.</p>
        </div>
    </div>
</body>
</html>
"""
    
    def _send_smtp_email(self, msg: MIMEMultipart, recipients: List[str]) -> bool:
        """Send email via SMTP"""
        
        try:
            print("📧 SMTP ile email gönderiliyor...")
            
            # Connect to Gmail SMTP server
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(self.smtp_user, self.smtp_password)
            
            # Send email
            text = msg.as_string()
            server.sendmail(self.smtp_user, recipients, text)
            server.quit()
            
            print(f"✅ Email başarıyla gönderildi: {', '.join(recipients)}")
            return True
            
        except Exception as e:
            print(f"❌ SMTP gönderim hatası: {e}")
            raise
    
    def _simulate_email_send(
        self, 
        html_file: str, 
        early_momentum_count: int, 
        trend_candidates_count: int, 
        portfolio_alerts: int
    ) -> None:
        """Simulate email sending when SMTP is not configured"""
        
        recipients = self._parse_recipients(self.recipient_email) if self.recipient_email else ["test@example.com"]
        subject = self._generate_email_subject(early_momentum_count, trend_candidates_count, portfolio_alerts)
        
        print(f"""
📧 EMAIL SİMÜLASYONU
──────────────────
📮 Kime: {', '.join(recipients)}
📝 Konu: {subject}
📎 Ek: {os.path.basename(html_file) if html_file else 'Yok'}
📊 Özet: {early_momentum_count} Erken Momentum, {trend_candidates_count} Güçlü Trend
{"⚠️  " + str(portfolio_alerts) + " Portföy Uyarısı" if portfolio_alerts > 0 else "✅ Portföy uyarısı yok"}
──────────────────
""")
    
    def test_email_connection(self) -> bool:
        """Test SMTP connection and credentials"""
        
        if not self.can_send_email():
            print("❌ SMTP bilgileri eksik:")
            print(f"   SMTP_USER: {'✅' if self.smtp_user else '❌'}")
            print(f"   SMTP_PASSWORD: {'✅' if self.smtp_password else '❌'}")
            print(f"   RECIPIENT_EMAIL: {'✅' if self.recipient_email else '❌'}")
            return False
        
        try:
            print("🔍 SMTP bağlantısı test ediliyor...")
            
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(self.smtp_user, self.smtp_password)
            server.quit()
            
            print("✅ SMTP bağlantısı başarılı!")
            return True
            
        except Exception as e:
            print(f"❌ SMTP test hatası: {e}")
            return False
    
    def send_decision_report_email(
        self,
        html_file: str,
        sat_count: int = 0,
        azalt_count: int = 0,
        al_count: int = 0,
        tut_count: int = 0,
        bekle_count: int = 0,
        alma_count: int = 0,
        whatsapp_summary: str = ""
    ) -> bool:
        """
        Karar Raporu email gönder
        
        Args:
            html_file: HTML rapor dosyası
            sat_count: SAT sinyali sayısı
            azalt_count: AZALT sinyali sayısı
            al_count: AL sinyali sayısı
            tut_count: TUT sinyali sayısı
            bekle_count: BEKLE sinyali sayısı
            alma_count: ALMA sinyali sayısı
            whatsapp_summary: WhatsApp formatında özet
        """
        
        if not self.can_send_email():
            print("⚠️ Email gönderimi simüle ediliyor (SMTP bilgileri eksik)")
            self._simulate_decision_email(sat_count, azalt_count, al_count, tut_count, bekle_count, alma_count)
            return False
        
        try:
            recipients = self._parse_recipients(self.recipient_email)
            
            # Email subject
            today = datetime.now().strftime('%d/%m/%Y')
            urgent = "🚨 " if sat_count > 0 else ""
            subject = f"{urgent}TEFAS Karar Raporu {today} | SAT:{sat_count} AL:{al_count} TUT:{tut_count}"
            
            msg = MIMEMultipart()
            msg['From'] = self.smtp_user
            msg['To'] = ', '.join(recipients)
            msg['Subject'] = subject
            
            # Email body (WhatsApp format dahil)
            body = self._generate_decision_email_body(
                sat_count, azalt_count, al_count, tut_count, bekle_count, alma_count, whatsapp_summary
            )
            msg.attach(MIMEText(body, 'html', 'utf-8'))
            
            # HTML dosyasını ekle
            if html_file and os.path.exists(html_file):
                with open(html_file, 'rb') as attachment:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment.read())
                
                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename= {os.path.basename(html_file)}'
                )
                msg.attach(part)
            
            return self._send_smtp_email(msg, recipients)
            
        except Exception as e:
            print(f"❌ Email gönderim hatası: {e}")
            self._simulate_decision_email(sat_count, azalt_count, al_count, tut_count, bekle_count, alma_count)
            return False
    
    def _generate_decision_email_body(
        self,
        sat_count: int,
        azalt_count: int,
        al_count: int,
        tut_count: int,
        bekle_count: int,
        alma_count: int,
        whatsapp_summary: str
    ) -> str:
        """Karar raporu email gövdesi"""
        
        # WhatsApp özetini HTML'e dönüştür
        whatsapp_html = whatsapp_summary.replace('\n', '<br>').replace('•', '•') if whatsapp_summary else ""
        
        # Acil durum uyarısı
        urgent_section = ""
        if sat_count > 0:
            urgent_section = f"""
            <div style="background: #f8d7da; border: 2px solid #dc3545; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <h2 style="color: #dc3545; margin: 0;">🚨 ACİL: {sat_count} FON SAT SINYALİ VERİYOR!</h2>
                <p style="margin: 10px 0 0 0;">Portföyünüzde sat sinyali veren fonlar var. Lütfen detaylı raporu inceleyin.</p>
            </div>
            """
        
        return f"""
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TEFAS Karar Raporu</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 20px; background: #1a1a2e; color: #fff; }}
        .container {{ max-width: 600px; margin: 0 auto; background: #16213e; padding: 30px; border-radius: 12px; }}
        .header {{ background: linear-gradient(135deg, #00d9ff 0%, #00ff88 100%); color: #000; padding: 25px; border-radius: 8px; text-align: center; margin-bottom: 25px; }}
        .header h1 {{ margin: 0; font-size: 1.8em; }}
        .summary {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin: 20px 0; }}
        .summary-card {{ background: rgba(255,255,255,0.05); padding: 15px; border-radius: 8px; text-align: center; border: 1px solid rgba(255,255,255,0.1); }}
        .summary-number {{ font-size: 2em; font-weight: bold; }}
        .sat {{ color: #ff0000; border-color: #ff0000; }}
        .azalt {{ color: #ff6b35; border-color: #ff6b35; }}
        .al {{ color: #00ff88; border-color: #00ff88; }}
        .tut {{ color: #ffd700; border-color: #ffd700; }}
        .bekle {{ color: #00d9ff; border-color: #00d9ff; }}
        .alma {{ color: #ff4757; border-color: #ff4757; }}
        .whatsapp-box {{ background: #25D366; color: #fff; padding: 20px; border-radius: 8px; margin: 20px 0; font-family: monospace; font-size: 14px; }}
        .footer {{ text-align: center; margin-top: 30px; padding: 20px; color: #888; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔥 TEFAS Karar Raporu</h1>
            <p style="margin: 10px 0 0 0;">📅 {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
        </div>
        
        {urgent_section}
        
        <div class="summary">
            <div class="summary-card sat">
                <div class="summary-number">{sat_count}</div>
                <div>🔴 SAT</div>
            </div>
            <div class="summary-card azalt">
                <div class="summary-number">{azalt_count}</div>
                <div>⚠️ AZALT</div>
            </div>
            <div class="summary-card al">
                <div class="summary-number">{al_count}</div>
                <div>✅ AL</div>
            </div>
        </div>
        
        <div class="summary">
            <div class="summary-card tut">
                <div class="summary-number">{tut_count}</div>
                <div>🟡 TUT</div>
            </div>
            <div class="summary-card bekle">
                <div class="summary-number">{bekle_count}</div>
                <div>⏳ BEKLE</div>
            </div>
            <div class="summary-card alma">
                <div class="summary-number">{alma_count}</div>
                <div>❌ ALMA</div>
            </div>
        </div>
        
        <div class="whatsapp-box">
            <strong>📱 Hızlı Özet:</strong><br><br>
            {whatsapp_html if whatsapp_html else "Detaylar için HTML raporu açın."}
        </div>
        
        <div style="background: rgba(0,255,136,0.1); padding: 15px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #00ff88;">
            <h3 style="margin: 0 0 10px 0;">📋 Detaylı Rapor</h3>
            <p style="margin: 0;">Ekli HTML dosyasında tüm kararları, RSI/MACD değerlerini ve stratejileri bulabilirsiniz.</p>
        </div>
        
        <div class="footer">
            <p>🤖 TEFAS Decision Engine v2.0 tarafından otomatik gönderildi</p>
        </div>
    </div>
</body>
</html>
"""
    
    def _simulate_decision_email(
        self,
        sat_count: int,
        azalt_count: int,
        al_count: int,
        tut_count: int,
        bekle_count: int,
        alma_count: int
    ) -> None:
        """Karar raporu email simülasyonu"""
        
        recipients = self._parse_recipients(self.recipient_email) if self.recipient_email else ["test@example.com"]
        today = datetime.now().strftime('%d/%m/%Y')
        
        print(f"""
📧 KARAR RAPORU EMAIL SİMÜLASYONU
──────────────────────────────
📭 Kime: {', '.join(recipients)}
📝 Konu: TEFAS Karar Raporu {today}
📊 Özet:
   🔴 SAT: {sat_count}
   ⚠️ AZALT: {azalt_count}
   ✅ AL: {al_count}
   🟡 TUT: {tut_count}
   ⏳ BEKLE: {bekle_count}
   ❌ ALMA: {alma_count}
──────────────────────────────
""")
    
    def send_test_email(self) -> bool:
        """Send a test email to verify configuration"""
        
        if not self.can_send_email():
            print("⚠️ Test email simüle ediliyor...")
            self._simulate_email_send("test_report.html", 2, 3, 1)
            return False
        
        try:
            recipients = self._parse_recipients(self.recipient_email)
            
            msg = MIMEMultipart()
            msg['From'] = self.smtp_user
            msg['To'] = ', '.join(recipients)
            msg['Subject'] = f"TEFAS Test Email - {datetime.now().strftime('%d/%m/%Y %H:%M')}"
            
            body = f"""
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <title>TEFAS Test Email</title>
</head>
<body style="font-family: Arial, sans-serif; margin: 20px;">
    <div style="background: #007bff; color: white; padding: 20px; border-radius: 8px;">
        <h1>🧪 TEFAS Email Testi</h1>
        <p>Bu test email sisteminizin düzgün çalıştığını doğrulamak için gönderildi.</p>
    </div>
    <div style="margin: 20px 0; padding: 15px; background: #f8f9fa; border-radius: 8px;">
        <h3>✅ Test Başarılı</h3>
        <p>SMTP ayarlarınız doğru ve email gönderimi aktif!</p>
        <p><strong>Zaman:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>
    </div>
</body>
</html>
"""
            
            msg.attach(MIMEText(body, 'html', 'utf-8'))
            
            return self._send_smtp_email(msg, recipients)
            
        except Exception as e:
            print(f"❌ Test email hatası: {e}")
            return False


if __name__ == "__main__":
    # Test email reporter
    email_reporter = EmailReporter()
    print("📧 EmailReporter sınıfı hazır!")
    print(f"SMTP yapılandırması: {'✅' if email_reporter.can_send_email() else '❌'}")
    
    # Test connection if configured
    if email_reporter.can_send_email():
        email_reporter.test_email_connection()