import smtplib
from email.message import EmailMessage
from email.utils import make_msgid
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.application import MIMEApplication
import mimetypes
import re
import os

class EmailSender:
    def __init__(self, 
                 sender_email,
                 password, 
                 cc_emails=[],
                 suffix_content="", 
                 suffix_addresses=['ACS_icon.png', 'tele_icon.png', 'mail_icon.png', 'link_icon.png', 'location_icon.png'], 
                 template_title=None, 
                 template_content=None, 
                 set_match_dict={}, 
                 smtp_server="mail.acsunshine.com", 
                 smtp_port=465,
                 encoding='utf-8'):
        self.sender_email = sender_email
        self.password = password
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.suffix_content = suffix_content
        self.suffix_addresses = suffix_addresses
        self.encoding = encoding
        self.cc_emails = cc_emails

#        if not(template_title is None) and os.path.isfile(template_title):
#            with open(template_title, 'r') as file:
#                self.template_title = file.read()
#        else:
#            self.template_title = template_title
#
#        if not(template_content is None) and os.path.isfile(template_content):
#            with open(template_content, 'r') as file:
#                self.template_content = file.read()
#        else:
#            self.template_content = template_content
    
        self.template_title = self.set_template_title(template_title)
        self.template_content = self.set_template_content(template_content)
        self.set_match_dict = set_match_dict
    
    def set_template_title(self, template_title):
        if not(template_title is None) and os.path.isfile(template_title):
            with open(template_title, 'r', encoding=self.encoding) as file:
                self.template_title = file.read()
        else:
            self.template_title = template_title
        return "Template Title: ", self.template_title
    
    def set_template_content(self, template_content):
        if not(template_content is None) and os.path.isfile(template_content):
            print(template_content, self.encoding)
            with open(template_content, 'r', encoding=self.encoding) as file:
                self.template_content = file.read()
        else:
            self.template_content = template_content
        return "Template Content: ", self.template_content

    def set_match_dict(self, match_dict):
        self.set_match_dict = match_dict

    def add_suffix_address(self, _path):
        if not (_path is None) and os.path.isfile(_path):
            self.suffix_addresses.append(_path)
            return _path

    def send_with_content_replacement(self, 
                                      customer_email,
                                      attachment_addresses=[], 
                                      customer_info={}, 
                                      match_dict=None, 
                                      template_title=None, 
                                      template_content=None):
        if match_dict is None:
            match_dict = self.set_match_dict
        if template_title is None:
            template_title = self.template_title
        if template_content is None:
            template_content = self.template_content
        
        placeholders = re.findall(r'\$\$(.*?)\$\$', template_content)
        placeholders += re.findall(r'\$\$(.*?)\$\$', template_title)
        print("placeholders: ", placeholders)

        reverse_match_dict = {}
        for key, values in match_dict.items():
            for value in values:
                reverse_match_dict[value] = key
        #print(reverse_match_dict)
        
        for placeholder in placeholders:
            #print(placeholder)
        # Find the corresponding key in customer_info using reverse_match_dict
            if placeholder in reverse_match_dict:
                key = reverse_match_dict[placeholder]
                if key in customer_info:
                    # Replace the placeholder with the corresponding value from customer_info
                    template_content = template_content.replace(f'$${placeholder}$$', customer_info[key])
                    template_title = template_title.replace(f'$${placeholder}$$', customer_info[key])
        
        print("template title: ", template_title)
        self.send_email(customer_emails=[customer_email], 
                        attachment_addresses=attachment_addresses,
                        template_title=template_title, 
                        template_content=template_content
                        )
        print("Send to "+customer_email+": "+template_title)

        return

    def send_email(self, customer_emails, attachment_addresses=[], template_title=None, template_content=None):

        if template_title is None:
            template_title = self.template_title
        if template_content is None:
            template_content = self.template_content

        # SMTP server details
        smtp_server = "mail.acsunshine.com"
        smtp_port = 465  # Port for TLS

        # Setting up the SMTP server with TLS
        with smtplib.SMTP_SSL(smtp_server, smtp_port) as smtp:
            #smtp.starttls()  # Start TLS encryption
            smtp.login(self.sender_email, self.password)

            # Create the email message
            msg = MIMEMultipart('related')
            msg['Subject'] = template_title
            msg['From'] = self.sender_email
            msg['Cc'] = ', '.join(self.cc_emails)

            # Create the HTML part
            html_part = MIMEMultipart('alternative')
            msg.attach(html_part)

            # Prepare the HTML content with placeholders for images
            html_content = template_content +"\n"+ self.suffix_content

            # Replace placeholders with actual image tags and attach images
            for i, picture_address in enumerate(self.suffix_addresses, start=0):
                mime_type, _ = mimetypes.guess_type(picture_address)
                mime_type, mime_subtype = mime_type.split('/')
                image_cid = make_msgid()  # Create a unique Content-ID for the image

                # Create image tag
                img_tag = f'img src="cid:{image_cid[1:-1]}" '

                # Replace placeholder in HTML content
                html_content = html_content.replace(f'img src="{picture_address}" ', img_tag)

                # Attach the image
                with open(picture_address, 'rb') as file:
                    img_data = file.read()

                    image = MIMEImage(img_data, _subtype=mime_subtype, name=picture_address.split('/')[-1])
                    image.add_header('Content-ID', image_cid)

                    #image = MIMEImage(img_data, name=os.path.basename(picture_address))
                    #image.add_header('Content-ID', '<image'+str(i)+'>')
                    #image.add_header('Content-Disposition', 'inline', filename=os.path.basename(picture_address))

                    #print(picture_address)
                    msg.attach(image)

            # Attach the HTML content to the email
            html_part.attach(MIMEText(html_content, 'html'))

            # Attach any additional files
            for attachment in attachment_addresses:
                mime_type, _ = mimetypes.guess_type(attachment)
                mime_type, mime_subtype = mime_type.split('/')

                with open(attachment, 'rb') as file:
                    attachment_data = file.read()
                    mime_attachment = MIMEApplication(attachment_data, _subtype=mime_subtype)
                    mime_attachment.add_header('Content-Disposition', 'attachment', filename=attachment.split('/')[-1])
                    msg.attach(mime_attachment)

            # Send the email to all customers
            for customer_email in customer_emails:
                msg['To'] = customer_email
                smtp.send_message(msg)
                print(f"Email sent to {customer_email}")
                # Clear the 'To' field for the next recipient
                del msg['To']
