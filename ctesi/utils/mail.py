from ctesi import app
import smtplib

def send_mail(recipient, subject, body):
    sender = app.config['MAIL_DEFAULT_SENDER'][0]
    msg = 'From: {}\nTo: {}\nSubject: {}\n\n{}\n\n.'.format(sender, recipient, subject, body)

    server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
    server.ehlo()
    server.login(app.config['MAIL_USERNAME'][0], app.config['MAIL_PASSWORD'])

    server.sendmail(sender, recipient, msg)

    return server.quit()
