from rocon_client_sdk_py.virtual_core.components.button_requests import ButtonRequests
import pydash

class HookBusy():
    def __init__(self, context):
        self._context = context

    async def checkRevision(self, report):

        br = ButtonRequests(self._context)
        proposed_instructions = pydash.get(report, 'revision.propositions.instructions')
        if proposed_instructions is None:
            return True

        #TODO 정확한지 확인
        diff_insts = pydash.difference_with(proposed_instructions, report['instructions'], pydash.is_equal)

        for inst in diff_insts:
            def cb(result, value):
                result[value['key']] = value
                return result

            args = pydash.reduce_(inst['action']['args'], cb)
            if inst['action']['func_name'] == 'wait':

                if args['param']['value'] == 'success':
                    request = br.find_request_by_button_id('signal', self._context.worker.uuid)
                    if report:
                        await self._context.api_report.approve_revision(report)
                        br.process(request, 'success')
                    else:
                        print('found revision to finish wait(signal) but there is no button request for it')
                else:
                    print('condition is not match on wait')

            else:
                print('cannot handle revision of instruction')

        return True