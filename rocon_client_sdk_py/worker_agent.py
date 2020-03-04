import asyncio
import threading
from rocon_client_sdk_py.server.web_server import WebServer
import paho.mqtt.client as mqtt
from rocon_client_sdk_py.worker import Worker

class WorkerAgent():
    def __init__(self):

        self._event_loop = asyncio.get_event_loop()

        def f(loop):
            asyncio.set_event_loop(loop)
            loop.run_forever()

        self._event_thread = threading.Thread(target=f, args=(self._event_loop,))
        self._event_thread.start()

        self.mqtt_client = None

        self._worker = self.on_create(self._event_loop)

        self._worker.set_after_tick_callback(self._callback_after_tick)


        # start web server
        port = self._worker._options['configs']['server']['port']
        self._web_server = WebServer(self, port)
        asyncio.run_coroutine_threadsafe(self._web_server.start(), self._event_loop)

        # register into WorkerPool
        api_pool = self._worker.context.api_worker_pool
        reg_data = {
            'uuid': self._worker.uuid,
            'hostWorkerAgent': 'localhost',
            'portWorkerAgent': port
        }
        asyncio.run_coroutine_threadsafe(api_pool.register_worker(self._worker.uuid, reg_data), self._event_loop)


    @property
    def worker(self):
        return self._worker

    @property
    def uuid(self):
        return self._worker.uuid

    @property
    def context(self):
        return self._worker.context

    def run(self):
        input_cmd = ''
        while input_cmd.lower() != 'q':
            input_cmd = input('Enter "q" to quilt\n>')

            cmd = input_cmd.lower()
            if cmd == 't':
                if self._worker:
                    self._worker.tick()
            elif cmd == 'r':  # start tick timer
                if self._worker:
                    self._worker.start_tick_timer(1000)
            elif cmd == 's':
                if self._worker:
                    self._worker.stop_tick_timer()

        self.on_destroy()

    def on_create(self) -> Worker:
        print('on_create')

        return None

    def on_destroy(self):
        print('on_destroy')

        self._worker.close_mqtt()
        self._event_loop.call_soon_threadsafe(self._event_loop.stop)

        print('loop is closed? : ' + str(self._event_loop.is_closed()))
        print('event_thread alive? : ' + str(self._event_thread.is_alive()))


    def mqtt_on_connect(self, client, userdata, flags, rc):
        print('Connected with result code' + str(rc))
        client.subscribe('tree/')  #

    def mqtt_on_message(self, client, userdata, msg):
        print(msg.topic + ' ' + str(msg.payload))

        #self.mqtt_publish(msg.payload)

    def mqtt_publish(self, payload):
        if self.mqtt_client == None:
            self.start_mqtt()

        self.mqtt_client.publish('tree/{}'.format(self._worker.uuid), payload)


    def start_mqtt(self):
        # mqtt subscribe
        if self.mqtt_client is None:
            self.close_mqtt()

        self.mqtt_client = mqtt.Client()
        self.mqtt_client.on_connect = self.mqtt_on_connect
        self.mqtt_client.on_message = self.mqtt_on_message

        self.mqtt_client.connect('localhost', port=10997)
        self.mqtt_client.loop_start()

    def close_mqtt(self):
        if self.mqtt_client:
            self.mqtt_client.loop_stop()
            self.mqtt_client.disconnect()
            self.mqtt_client = None

        print('closed mqtt')

    def restart(self):
        self.stop()
        self._worker.reset()

    def start(self, interval_msec = 1000):
        self._worker.start(interval_msec)
        self.start_mqtt()

    def stop(self, offline = False):
        self._worker.stop(offline)
        self.close_mqtt()

    def start_tick_timer(self, interval):
        self._worker.start_tick_timer(interval)

    def _callback_after_tick(self, context):
        publishing_data = context.get_trees_stringify()

        self.mqtt_publish(publishing_data)