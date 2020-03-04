import py_trees
from .constants import *
import pydash
import asyncio

class BlackboardManager():
    def __init__(self, context):

        #py_trees.blackboard.Blackboard.enable_activity_stream(maximum_size=100)

        self._board = py_trees.blackboard.Client(name=MASTER_BLACKBOARD_NAME)
        self._board.register_key(key=KEY_CONTEXT, access=py_trees.common.Access.WRITE)
        self._board.context = context

        context.blackboard = self

    @property
    def context(self):
        return self._board.context

    def get(self, key):

        if self._board.is_registered(key, py_trees.common.Access.READ):
            #print(self._board.get(key))
            # return self._board[key]
            return self._board.get(key)

        else:
            return None

    def set(self, key, value):
        self._board.register_key(key=key, access=py_trees.common.Access.READ)
        self._board.register_key(key=key, access=py_trees.common.Access.WRITE)
        self._board.set(key, value)
        #self._board[key] = value
        #print(self._board[key])

        if key == 'status':
            self.set_worker({'status': value})


    def get_sub(self, key, sub_key):
        data = self.get(key)
        if data:
            return data[sub_key]
        else:
            return None

    def get_worker(self, sub_key=None):
        if sub_key is None:
            org_worker = self.get('worker')
            update = self.get_worker_update()

            if org_worker is None:
                return update

            if update is None:
                return org_worker

            worker = pydash.assign({}, org_worker, update)
            #print(worker)
            return worker
        else:
            return self.get_sub('worker', sub_key)

    def set_worker(self, update):

        wu = self.get('worker_update')
        if wu:
            worker_update = pydash.assign({}, wu, update)
        else:
            worker_update = pydash.assign({}, update)
        #print(worker_update)
        self.set('worker_update', worker_update)

    def get_worker_update(self):
        return self.get('worker_update')

    def set_worker_update(self, update):
        worker_update = self.get('worker_update')
        if worker_update:
            new_update = pydash.assign({}, worker_update, update)
        else:

            new_update = pydash.assign({}, update)

        self.set('worker_update', new_update)

    def get_update_worker_body(self):
        update = self.get_worker_update() or {}
        worker = self.get_worker()

        for key in update:
            if worker and worker.get(key):
                update[key] = worker[key]

        """
        def cb(value, key):
            if worker and worker.get(key):
                try:
                    if key in worker:
                        # print(worker[key])
                        update[key] = worker[key]
                except Exception as err:
                    print(err)

        pydash.for_each(update, cb)
        """
        return update

    async def sync_worker(self):
        if self.get_worker_update() is None:
            return self.get_worker()


        #print(update)
        worker = self.get_worker()
        body = self.get_update_worker_body()

        assert(worker is not None)

        updated_worker = await self.context.api_worker.update_worker(worker['id'], body)
        self.context.blackboard.set('worker', updated_worker)
        self.context.blackboard.set('worker_update', None)

        worker = self.get_worker()

        return worker


    def get_report(self):

        org_report = self.get('report')
        update = self.get_report_update()

        if org_report is None:
            return update

        if update is None:
            return org_report

        report = pydash.assign({}, org_report, update)
        print(report)
        return report


    def set_report(self, update):
        if update is None:
            self.set('report_update', {})
            return

        ru = self.get('report_update')
        if ru:
            report_update = pydash.assign({}, ru, update)
        else:
            report_update = pydash.assign({}, update)
        print(report_update)
        self.set('report_update', report_update)

    def get_report_update(self):
        return self.context.blackboard.get('report_update')

    def set_report_update(self, update):
        return self.context.blackboard.set('report_update', update)

    def get_update_report_body(self):
        update = self.get_report_update() or {}
        report = self.get_report()

        for key in update:
            if report and report.get(key):
                update[key] = report[key]

        return update

    async def sync_report(self):
        worker = self.get_worker()
        body = self.get_update_report_body()

        body['worker'] = worker['id']
        report = self.get_report()

        updated_report = await self.context.api_report.update_report(report['id'], body)
        self.context.blackboard.set('report', updated_report)
        self.context.blackboard.set('report_update', None)

        return self.get_report()


    def clear_report(self):
        self.context.blackboard.set('report', None)
        self.context.blackboard.set('report_update', None)

    def update_report_result(self, result):
        report = self.get_report()
        if report is None:
            print('report is None')

        if 'result' in report:
            updated_result = report['result']
        else:
            updated_result = {}

        if 'status' in result and result['status']:
            pydash.set_(updated_result, 'status', result['status'])

        if 'status_msg' in result and result['status_msg']:
            pydash.set_(updated_result, 'status_msg', result['status_msg'])

        if 'returns' in result and result['returns']:
            pydash.set_(updated_result, 'returns', result['returns'])

        if 'current' in result and result['current']:
            pydash.set_(updated_result, 'current', result['current'])


        self.context.blackboard.set_report({'result': updated_result})


    def update_instruction_result(self, result):
        report = self.context.blackboard.get_report()
        returns = pydash.get(report, 'result.returns') or []
        idx = pydash.find_index(returns, {'id': result['id']})
        if idx != -1:
            returns[idx] = pydash.assign({}, returns[idx], result)
        else:
            returns.append(result)

        self.update_report_result({'returns': returns})

    #def _get_blackboard_info(self):
    """
        'trees' 구조 
        {
          trees: {
            '1ac7f790-0cb2-4855-b72a-3dba48c6b5e1': { tree: [Object], treeMemory: [Object], node: [Object] }
          },
          shared: {}
        }
    """

    def get_blackborad_info(self):

        dic_data = {
            'trees': {},
            'shared': {}
        }



        id = self.context.worker.tree_manager.get_tree_id()
        dic_data['trees'][str(id)] = {
            'tree': {
                # 생략
            },
            'treeMemory': {
                # 생략
            },
            'node': self.get_all_node_status()
        }

        return dic_data

    def get_all_node_status(self):
        tree_mgr = self._board.context.worker.tree_manager
        return tree_mgr.get_trees_status()


    def get_blackboard_data(self):
        data = {
            'trees': pydash.reduce_()
        }

        return data

    def reset_blackboard(self):
        #py_trees.blackboard.Blackboard.
        print(self._board)
        #py_trees.blackboard.ActivityStream.clear()
        #self._board.unregister_all_keys()
        print(self._board)
        print('reset_blackboard')