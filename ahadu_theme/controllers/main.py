import hashlib
import odoo
from odoo import http
from odoo.tools import pycompat
from odoo.tools.translate import _
from odoo.http import request
from odoo.addons.web.controllers.home import Home as WebHome
from odoo.addons.web.controllers.utils import ensure_db, _get_login_redirect_url,is_user_internal

# Shared parameters for all login/signup flows
# SIGN_UP_REQUEST_PARAMS = {'db', 'login', 'debug', 'token', 'message', 'error',
#                           'scope', 'mode', 'redirect', 'redirect_hostname',
#                           'email', 'name', 'partner_id', 'password',
#                           'confirm_password', 'city', 'country_id', 'lang'}


# Shared parameters for all login/signup flows
SIGN_UP_REQUEST_PARAMS = {'db', 'login', 'debug', 'token', 'message', 'error', 'scope', 'mode',
                          'redirect', 'redirect_hostname', 'email', 'name', 'partner_id',
                          'password', 'confirm_password', 'city', 'country_id', 'lang', 'signup_email'}
LOGIN_SUCCESSFUL_PARAMS = set()

CREDENTIAL_PARAMS = ['login', 'password', 'type']
def _login_redirect(self, uid, redirect=None):
    return _get_login_redirect_url(uid, redirect)

class Home(WebHome):
    @http.route(route='/web/login', type='http', auth="none")
    def web_login(self, redirect=None, **kw):
        """Override web_login function to add features of this module."""
        ensure_db()
        request.params['login_success'] = False
        if request.httprequest.method == 'GET' and redirect and request.session.uid:
            return request.redirect(redirect)

        if request.env.uid is None:
            if request.session.uid is None:
                # no user -> auth=public with specific website public user
                request.env["ir.http"]._auth_method_public()
            else:
                # auth=user
                request.update_env(user=request.session.uid)

        values = {k: v for k, v in request.params.items() if k in SIGN_UP_REQUEST_PARAMS}
        try:
            values['databases'] = http.db_list()
        except odoo.exceptions.AccessDenied:
            values['databases'] = None

        if request.httprequest.method == 'POST':
            old_uid = request.update_env(user=request.session.uid)
            try:
                credential = {key: value for key, value in request.params.items() if key in CREDENTIAL_PARAMS and value}
                credential.setdefault('type', 'password')
                if request.env['res.users']._should_captcha_login(credential):
                    request.env['ir.http']._verify_request_recaptcha_token('login')
                auth_info = request.session.authenticate(request.env, credential)
                request.params['login_success'] = True
                return request.redirect(self._login_redirect(auth_info['uid'], redirect=redirect))
            except odoo.exceptions.AccessDenied as e:
                if e.args == odoo.exceptions.AccessDenied().args:
                    values['error'] = _("Wrong login/password")
                else:
                    values['error'] = e.args[0]
        else:
            if 'error' in request.params and request.params.get('error') == 'access':
                values['error'] = _('Only employees can access this database. Please contact the administrator.')

        if 'login' not in values and request.session.get('auth_login'):
            values['login'] = request.session.get('auth_login')

        if not odoo.tools.config['list_db']:
            values['disable_database_manager'] = True

        conf_param = request.env['ir.config_parameter'].sudo()
        orientation = conf_param.get_param('ahadu_theme.orientation')
        image = conf_param.get_param('ahadu_theme.image')
        url = conf_param.get_param('ahadu_theme.url')
        background_type = conf_param.get_param('ahadu_theme.background')
        if background_type == 'color':
            values['bg'] = ''
            values['color'] = conf_param.sudo().get_param(
                'ahadu_theme.color')
        elif background_type == 'image':
            exist_rec = request.env['ir.attachment'].sudo().search(
                [('is_background', '=', True)])
            if exist_rec:
                exist_rec.unlink()
            attachments = request.env['ir.attachment'].sudo().create({
                'name': 'Background Image',
                'datas': image,
                'type': 'binary',
                'mimetype': 'image/png',
                'public': True,
                'is_background': True
            })
            base_url = conf_param.sudo().get_param('web.base.url')
            url = base_url + '/web/image?' + 'model=ir.attachment&id=' + str(
                attachments.id) + '&field=datas'
            values['bg_img'] = url or ''
        elif background_type == 'url':
            pre_exist = request.env['ir.attachment'].sudo().search(
                [('url', '=', url)])
            if not pre_exist:
                attachments = request.env['ir.attachment'].sudo().create({
                    'name': 'Background Image URL',
                    'url': url,
                    'type': 'url',
                    'public': True
                })
            else:
                attachments = pre_exist
            encode = hashlib.md5(
                pycompat.to_text(attachments.url).encode("utf-8")).hexdigest()[
                     0:7]
            encode_url = "/web/image/{}-{}".format(attachments.id, encode)
            values['bg_img'] = encode_url or ''
        if orientation == 'right':
            response = request.render('ahadu_theme.login_template_right',
                                      values)
        elif orientation == 'left':
            response = request.render('ahadu_theme.login_template_left',
                                      values)
        elif orientation == 'middle':
            response = request.render('ahadu_theme.login_template_middle',
                                      values)
        else:
            response = request.render('web.login', values)


        response.headers['Cache-Control'] = 'no-cache'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['Content-Security-Policy'] = "frame-ancestors 'self'"
        return response

    @http.route('/web/login_successful', type='http', auth='user', website=True, sitemap=False)
    def login_successful_external_user(self, **kwargs):
        """Landing page after successful login for external users (unused when portal is installed)."""
        valid_values = {k: v for k, v in kwargs.items() if k in LOGIN_SUCCESSFUL_PARAMS}
        return request.render('web.login_successful', valid_values)
