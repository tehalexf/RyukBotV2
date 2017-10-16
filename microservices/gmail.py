from hotswap.objects import ModularService
from apiclient import discovery
from oauth2client import client
_client = client
from oauth2client import tools
from oauth2client.file import Storage
from apiclient import errors
import os
import httplib2

class GmailService(ModularService):
    def __init__(self, port, service_name, manager_port, query_mode=False):
        ModularService.__init__(self, port, service_name, manager_port, query_mode = query_mode)
        self.wait_for_manager()

        self.client = _client
        self.SCOPES = 'https://mail.google.com/'
        self.CLIENT_SECRET_FILE = 'config/client_secret.json'
        self.APPLICATION_NAME = 'RyukBot API'
        credentials = self.get_credentials()
        http = credentials.authorize(httplib2.Http())
        self.service = discovery.build('gmail', 'v1', http=http)
        self.get_credentials()


    def ListMessagesMatchingQuery(self, service, user_id, query=''):
      """List all Messages of the user's mailbox matching the query.

      Args:
        service: Authorized Gmail API service instance.
        user_id: User's email address. The special value "me"
        can be used to indicate the authenticated user.
        query: String used to filter messages returned.
        Eg.- 'from:user@some_domain.com' for Messages from a particular sender.

      Returns:
        List of Messages that match the criteria of the query. Note that the
        returned list contains Message IDs, you must use get with the
        appropriate ID to get the details of a Message.
      """
      try:
        response = service.users().messages().list(userId=user_id,
                                                  q=query).execute()
        messages = []
        if 'messages' in response:
          messages.extend(response['messages'])

        while 'nextPageToken' in response:
          page_token = response['nextPageToken']
          response = service.users().messages().list(userId=user_id, q=query,
                                            pageToken=page_token).execute()
          messages.extend(response['messages'])

        return messages
      except error:
        stdout ('An error occurred: %s' % error, SYS)


    def ListMessagesWithLabels(self, service, user_id, label_ids=[]):
      """List all Messages of the user's mailbox with label_ids applied.

      Args:
        service: Authorized Gmail API service instance.
        user_id: User's email address. The special value "me"
        can be used to indicate the authenticated user.
        label_ids: Only return Messages with these labelIds applied.

      Returns:
        List of Messages that have all required Labels applied. Note that the
        returned list contains Message IDs, you must use get with the
        appropriate id to get the details of a Message.
      """
      try:
        response = service.users().messages().list(userId=user_id,
                                                  labelIds=label_ids).execute()
        messages = []
        if 'messages' in response:
          messages.extend(response['messages'])

        while 'nextPageToken' in response:
          page_token = response['nextPageToken']
          response = service.users().messages().list(userId=user_id,
                                                    labelIds=label_ids,
                                                    pageToken=page_token).execute()
          messages.extend(response['messages'])

        return messages
      except error:
        stdout ('An error occurred: %s' % error, SYS)

    def GetMessage(self, service, user_id, msg_id):
      """Get a Message with given ID.

      Args:
        service: Authorized Gmail API service instance.
        user_id: User's email address. The special value "me"
        can be used to indicate the authenticated user.
        msg_id: The ID of the Message required.

      Returns:
        A Message.
      """
      try:
        message = service.users().messages().get(userId=user_id, id=msg_id).execute()

        return message
      except error:
        stdout ('An error occurred: %s' % error, SYS)

    def GetMimeMessage(self, service, user_id, msg_id):
      """Get a Message and use it to create a MIME Message.

      Args:
        service: Authorized Gmail API service instance.
        user_id: User's email address. The special value "me"
        can be used to indicate the authenticated user.
        msg_id: The ID of the Message required.

      Returns:
        A MIME Message, consisting of data from Message.
      """
      try:
        message = service.users().messages().get(userId=user_id, id=msg_id,
                                                format='raw').execute()

        msg_str = base64.urlsafe_b64decode(message['raw'].encode('ASCII'))

        mime_msg = email.message_from_string(msg_str)

        return mime_msg
      except error:
        stdout ('An error occurred: %s' % error, SYS)

    def SendToTrash(self, service, user_id, msg_id):
      """Send MIME message to trash.

      Args:
        service: Authorized Gmail API service instance.
        user_id: User's email address. The special value "me"
        can be used to indicate the authenticated user.
        msg_id: The ID of the Message required.

      Returns:
        None.
      """
      try:
        service.users().messages().trash(userId=user_id, id=msg_id).execute()
      except error:
        stdout ('An error occurred: %s' % error, SYS)


    def get_credentials(self):
        """Gets valid user credentials from storage.

        If nothing has been stored, or if the stored credentials  are invalid,
        the OAuth2 flow is completed to obtain the new credentials.

        Returns:
            Credentials, the obtained credential.  
        """
        try:
            import argparse
            flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
        except ImportError:
            flags = None
        credential_path = 'config/client_credentials.json'
        store = Storage(credential_path) 
        credentials = store.get()
        if not credentials or credentials.invalid:
            flow = _client.flow_from_clientsecrets(os.path.expandvars(self.CLIENT_SECRET_FILE), self.SCOPES)
            flow.user_agent = self.APPLICATION_NAME
            if flags:
                credentials = tools.run_flow(flow, store, flags)
            else: # Needed only for compatibility with Python 2.6
                credentials = tools.run(flow, store)
            print('Storing credentials to ' + credential_path, SYS)
        return credentials
    