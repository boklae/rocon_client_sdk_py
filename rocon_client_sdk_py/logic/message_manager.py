import ast
import os
import importlib.util
import glob, pathlib, sys

class MessageManager():
    def __init__(self, context, logger=None):
        self._context = context

        msg_path = context.worker.msg_def_paths
        self._msg_path = msg_path
        self._msg_instances = self._dynamic_load_messages(msg_path)
        self._msg_defines = {}

    def _dynamic_load_messages(self, msg_path):
        """
            주어진 절대경로 msg_path로 부터 message 클래스 인스턴스를 동적 생성한다.
            경로내의 message 정의 파일은 'message_xxx.py'의 규칙을 가져야한다.

        """
        msg_instances = {}

        sys.path.append(msg_path)
        py_files = glob.glob(os.path.join(msg_path, 'message_*.py'))
        for py_file in py_files:
            module_name = pathlib.Path(py_file).stem
            module = importlib.import_module(module_name)

            # path_name으로 부터 선언된 클래스 찾기 (내부 유일 클래스로 가정)
            msg_class = None
            # path_name = msg_path + '/' + filename
            with open(py_file, "rb") as src_stream:
                p = ast.parse(src_stream.read())
                classnames = [node.name for node in ast.walk(p) if isinstance(node, ast.ClassDef)]
                msg_class = classnames[0]

            class_instance = getattr(module, msg_class)
            msg = class_instance()
            msg_instances[msg.name] = msg
            print(msg.name)

        return msg_instances

    def find_message(self, msg_name):
        """
        msg_name (string)으로 message instance 찾아 리턴
        :return:
        """

        for msg_key in self._msg_instances:
            if self._msg_instances[msg_key].name == msg_name:
                return self._msg_instances[msg_key]

        return None

    async def execute(self, msg):
        msg_inst = self.find_message(msg['name'])
        # TODO validate message body schema using jsonschema

        if msg_inst:
            result = await msg_inst.on_handler(self._context, msg)
            return result
        else:
            print('malformed message handler: {}, {}'.format(msg['name'], {'message': msg}))
            return False

