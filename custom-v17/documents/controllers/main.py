import io
import zipfile

from odoo import http
from odoo.http import request


class ShareRoute(http.Controller):
    def _get_file_response(self, document_id, share_id=None, share_token=None, field='datas'):
        document = request.env['documents.document'].sudo().browse(document_id)
        if not document.exists():
            return request.not_found()

        content = document.datas or b''
        if isinstance(content, str):
            content = content.encode()
        filename = document.name or 'document'
        headers = [
            ('Content-Type', document.mimetype or 'application/octet-stream'),
            ('Content-Disposition', 'attachment; filename="%s"' % filename),
        ]
        return request.make_response(content, headers=headers)

    def _make_zip(self, filename, documents):
        mem_file = io.BytesIO()
        with zipfile.ZipFile(mem_file, mode='w', compression=zipfile.ZIP_DEFLATED) as archive:
            for document in documents:
                data = document.datas or b''
                if isinstance(data, str):
                    data = data.encode()
                archive.writestr(document.name or ('document_%s' % document.id), data)

        payload = mem_file.getvalue()
        headers = [
            ('Content-Type', 'application/zip'),
            ('Content-Disposition', 'attachment; filename="%s"' % filename),
        ]
        return request.make_response(payload, headers=headers)

    @http.route(['/document/share/<int:share_id>/<token>'], type='http', auth='public', website=True)
    def share_portal(self, share_id, token, **kwargs):
        share = request.env['documents.share'].sudo().browse(share_id)
        if not share.exists() or not share._check_token(token):
            return request.render('documents.not_available', {})
        return request.render('documents.share', {'share': share, 'token': token})

    @http.route(['/document/share/<int:share_id>/<token>/download/<int:document_id>'], type='http', auth='public', website=True)
    def share_download_single(self, share_id, token, document_id, **kwargs):
        share = request.env['documents.share'].sudo().browse(share_id)
        documents = share._get_documents_and_check_access(token)
        if not share.exists() or not documents:
            return request.not_found()
        if document_id not in documents.ids:
            return request.not_found()
        return self._get_file_response(document_id, share_id=share_id, share_token=token)

    @http.route(['/document/share/<int:share_id>/<token>/download_zip'], type='http', auth='public', website=True)
    def share_download_zip(self, share_id, token, **kwargs):
        share = request.env['documents.share'].sudo().browse(share_id)
        documents = share._get_documents_and_check_access(token)
        if not share.exists() or not documents:
            return request.not_found()
        filename = (share.name or 'documents').replace(' ', '_') + '.zip'
        return self._make_zip(filename, documents)
