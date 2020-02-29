import os
import uuid
from datetime import datetime

import boto3
import mailparser
import bleach
import talon
from talon.signature.bruteforce import extract_signature

from utils.models import IdeaModel, UserModel
from mail_templates.idea_received_confirmation.send_confirmation_idea_received import send_confirmation

AWS_REGION = os.environ['SES_AWS_REGION']
SES_S3_BUCKET_NAME = os.environ['SES_S3_BUCKET_NAME']
MAILBOX_ADDR = os.environ['MAILBOX_ADDR']
BASE_SITE_URL = f"https://{os.environ['DOMAIN_NAME']}/"
PUBLIC_VISIBILITY = 'PUBLIC'
NEW_TEXT_LINE = '\n'

s3 = boto3.client('s3')
ses = boto3.client('ses', region_name=AWS_REGION)
talon.init()

# TODO rename file to 'email_processor' or 'email_worker'
# or 'incoming_email'

def sanitize_title(raw_text):
    if not raw_text or not len(raw_text):
        return ''
    return bleach.clean(raw_text,
                        tags=[],
                        strip_comments=True, strip=True)

def sanitize_no_html_text(raw_text):
    if not raw_text or not len(raw_text):
        return ''
    return bleach.clean(raw_text,
                        tags=['br'],
                        strip_comments=True, strip=True)


def sanitize_idea_content(content):
    if not content or not len(content):
        return None
    return bleach.clean(content,
                        tags=['br', 'a', 's', 'em', 'u',
                              'ol', 'ul', 'li',
                              'h1', 'h2', 'h3', 'h4',
                              'sub', 'sup',
                              'del', 'blockquote', 'pre'],
                        attributes={'a': ['href']}, strip_comments=True, strip=True)


def clean_email_html(email_html_content):
    """ Email clients have various tags case and ways to split lines.
    1) lowering tags case
    2) converting p and div to br to unify formatting.
    3) sanitizing tags that are not allowed in content
    4) getting title from first line
    5) getting content from rest lines
    6) pack into div for compatibility with trix editor
    """
    text_like_html = sanitize_idea_content(
        email_html_content
        .replace('<DIV>', '<div>')
        .replace('</DIV>', '</div>')
        .replace('</P>', '</p>')
        .replace('<P>', '<p>')

        # FIX take into account: <br >, <br /> --> with a whitespace
        .replace('<br/>', '<br>')
        .replace('<BR/>', '<br>')
        .replace('<BR>', '<br>')

        .replace('<div>', '<br>')
        .replace('<div>', '')
        .replace('</div>', '<br>')
        .replace('<p>', '')
        .replace('</p>', '<br>')
        .replace('<br>', '<br>\n')
    )
    raw_content_lines = text_like_html.splitlines()
    content_lines = []
    while len(raw_content_lines) and not raw_content_lines[0]:
        raw_content_lines = raw_content_lines[1:]

    title = None
    if len(raw_content_lines):
        title = sanitize_title(raw_content_lines[0])
        if len(raw_content_lines) > 1:
            for line in raw_content_lines[1:]:
                if MAILBOX_ADDR in line:
                    if len(content_lines) > 0:
                        content_lines = content_lines[:-1]  # last line before quote is usually "XXX wrote:" or spacer.
                    break
                content_lines.append(line)

    text1 = f"<div>{NEW_TEXT_LINE.join(content_lines)}</div>"
    res = text1.replace(NEW_TEXT_LINE, '').replace('<br><br>', '<br>')
    # FIX take into account: <br >, <br /> --> with a whitespace


    return title, res


def clean_email_text(email_text_content):
    raw_content_lines = email_text_content.splitlines()
    title = None
    content_lines = []
    while len(raw_content_lines) and not raw_content_lines[0]:
        raw_content_lines = raw_content_lines[1:]
    if len(raw_content_lines):
        title = sanitize_title(raw_content_lines[0])
        if len(raw_content_lines) > 1:
            for line in raw_content_lines[1:]:
                if MAILBOX_ADDR in line or line.startswith('>'):
                    if len(content_lines) > 0:
                        content_lines = content_lines[:-1]  # last line before quote is usually "XXX wrote:" or spacer.
                    break
                content_lines.append(line + '<br>')

    text1 = sanitize_no_html_text(NEW_TEXT_LINE.join(content_lines))
    res = f"<div>{text1}</div>"

    return title, res


def get_cleaned_email(parsed_email):
    text_part = parsed_email.text_plain[0] if parsed_email.text_plain else None
    html_part = parsed_email.text_html[0] if parsed_email.text_html else None
    if not text_part and not html_part:
        return None, None

    body = None
    if text_part:
        body = clean_email_text(text_part)
    else:
        body = clean_email_html(html_part)


    body2, signature = extract_signature(body)
    print(f"striped out signature in the email: {signature}")

    # TODO optionally: if signature == None which may be 
    # because it's not been recognized, apply additionally:

    # from talon import signature
    # body3, signature = signature.extract(body2, sender='senders_email@example.com')


    return body2


# TODO rename to 'process_incoming_email'
def process_incoming_mail(parsed_email):
    from_email = parsed_email.from_
    found_users = UserModel.emailIndex.query(from_email[0][1])
    user = None
    for found_user in found_users:
        user = found_user
    if not user:
        # TOdo process email from user that dont registered
        return

    idea = IdeaModel(user.userId, str(uuid.uuid4()))
    title, content = get_cleaned_email(parsed_email)
    if title is None:
        return  # may be send notification about error?

    idea.content = content
    idea.title = title
    idea.authorName = user.name
    idea.authorSlug = user.slug
    idea.authorAvatar = user.avatar
    idea.createdDate = datetime.now()
    idea.visibility = PUBLIC_VISIBILITY
    idea_date_str = parsed_email.subject.split('[Daily Idea] Idea for ', 1)[1]
    idea.ideaDate = datetime.strptime(idea_date_str, '%a %b %d %Y')
    idea.likesCount = 0
    idea.commentsCount = 0
    idea.save()

    return idea


def endpoint(event, context):
    if 'ses' not in event['Records'][0]:
        print('this was not an SES event. event["Records"][0]["ses"] not found')
        return
    ses_notification = event['Records'][0]['ses']
    mail_message_id = ses_notification['mail']['messageId']
    print(f"Message Id received: {mail_message_id}")

    try:
        data = s3.get_object(Bucket=SES_S3_BUCKET_NAME, Key=mail_message_id)
        raw_email = data['Body'].read()
        parsed_email = mailparser.parse_from_string(raw_email.decode('utf-8'))
        idea = process_incoming_mail(parsed_email)
        send_confirmation(parsed_email.from_[0][1], idea, f"Re: {parsed_email.subject}")
    except Exception as e:
        print(e)
        raise e
