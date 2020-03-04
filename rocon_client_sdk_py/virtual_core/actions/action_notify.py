from rocon_client_sdk_py.virtual_core.actions.base import Action


class Notify(Action):
    def __init__(self):
        self.name = 'Notify'
        self.func_name = 'notify'

    async def on_define(self, context):
        print('define action of ' + self.name)

        return{
            'name': self.name,
            'func_name': self.func_name,
            'args':[
                {
                    'key': 'default_sender',
                    'name': 'Default Sender',
                    'domain': [],
                    'type': 'string',
                    'default': None,
                    'options': {
                        'user_input': True
                    }
                },
                {
                    'key': 'default_message',
                    'name': 'Default Message',
                    'domain': [],
                    'type': 'string',
                    'default': None,
                    'options': {
                        'user_input': True
                    }
                },
                {
                    'key': 'default_method',
                    'name': 'Default Method',
                    'type': 'object',
                    'properties': [
                        {
                            'key': 'email',
                            'name': 'E-mail',
                            'type': 'boolean',
                            'default': True
                        },
                        {
                            'key': 'sms',
                            'name': 'SMS',
                            'type': 'boolean',
                            'default': False
                        },
                        {
                            'key': 'web_push',
                            'name': 'Web_push',
                            'type': 'boolean',
                            'default': False
                        }
                    ]
                },
                {
                    'key': 'receivers',
                    'name': 'Receiver',
                    'domain': [],
                    'type': 'object',
                    'properties': [
                        {
                            'key': 'custom_sender',
                            'name': 'Custom Sender',
                            'domain': [],
                            'type': 'string',
                            'default': None,
                            'options': {
                                'user_input': True
                            }
                        },
                        {
                            'key': 'custom_message',
                            'name': 'Custom Message',
                            'domain': [],
                            'type': 'string',
                            'default': None,
                            'options': {
                                'user_input': True
                            }
                        },
                        {
                            'key': 'custom_method',
                            'name': 'Custom Method',
                            'type': 'object',
                            'properties': [
                                {
                                    'key': 'email',
                                    'name': 'E-mail',
                                    'type': 'boolean',
                                    'default': True
                                },
                                {
                                    'key': 'sms',
                                    'name': 'SMS',
                                    'type': 'boolean',
                                    'default': False
                                },
                                {
                                    'key': 'web_push',
                                    'name': 'Web_push',
                                    'type': 'boolean',
                                    'default': False
                                }
                            ]
                        },
                        {
                            'key': 'receiver_id',
                            'name': 'Receiver ID',
                            'domain': [],
                            'type': 'string',
                            'default': None,
                            'options': {
                                'user_input': True
                            }
                        },
                        {
                            'key': 'receiver_type',
                            'name': 'Receiver Type',
                            'domain': [],
                            'type': 'string',
                            'default': None,
                            'options': {
                                'user_input': True
                            }
                        }
                    ]
                }
            ]
        }

    async def on_perform(self, context, args):
        print('it is not implemented yet...')
        return True
