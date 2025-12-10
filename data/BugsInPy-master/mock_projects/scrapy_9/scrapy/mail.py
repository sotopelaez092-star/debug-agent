import logging
from email.mime.multipart import MIMEMultipart
from email.mime.nonmultipart import MIMENonMultipart
from email.utils import formatdate

# 缺少: from .utils.misc import arg_to_iter

logger = logging.getLogger(__name__)
COMMASPACE = ', '

class MailSender:
    """邮件发送器"""
    
    def __init__(self, mailfrom='noreply@example.com'):
        self.mailfrom = mailfrom
    
    def send(self, to, cc=None, subject='', body='', mimetype='text/plain'):
        """
        发送邮件
        
        Parameters
        ----------
        to : str or list
        cc : str or list
        """
        if '/' in mimetype:
            msg = MIMEMultipart()
        else:
            msg = MIMENonMultipart(*mimetype.split('/', 1))
        
        # 使用arg_to_iter但没有import
        to = list(arg_to_iter(to))  # ❌ NameError!
        cc = list(arg_to_iter(cc))  # ❌ NameError!
        
        msg['From'] = self.mailfrom
        msg['To'] = COMMASPACE.join(to)
        msg['Date'] = formatdate(localtime=True)
        msg['Subject'] = subject
        
        return msg
