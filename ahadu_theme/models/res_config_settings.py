from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    """Inherits 'res.config.settings' to add fields for customize login page."""
    _inherit = 'res.config.settings'

    orientation = fields.Selection(selection=[('default', 'Default'),
                                              ('left', 'Left'),
                                              ('middle', 'Middle'),
                                              ('right', 'Right')],
                                   string="Orientation",
                                   help="Type of login page visibility",
                                   config_parameter="ahadu_theme.orientation")
    background = fields.Selection(selection=[('color', 'Color Picker'),
                                             ('image', 'Image'),
                                             ('url', 'URL')],
                                  string="Background",
                                  help="Background of the login page",
                                  config_parameter="ahadu_theme.background")
    image = fields.Binary(string="Image", help="Select background image "
                                               "of login page")
    url = fields.Char(string="URL", help="Select and url of image",
                      config_parameter="ahadu_theme.url")
    color = fields.Char(string="Color", help="Set a colour for background "
                                             "of login page",
                        config_parameter="ahadu_theme.color")

    @api.model
    def get_values(self):
        """Super the get_values function to get the field values."""
        res = super(ResConfigSettings, self).get_values()
        params = self.env['ir.config_parameter'].sudo()
        res.update(image=params.get_param('ahadu_theme.image'))
        return res

    def set_values(self):
        """Super the set_values function to save the field values."""
        super(ResConfigSettings, self).set_values()
        params = self.env['ir.config_parameter'].sudo()
        params.set_param('ahadu_theme.image', self.image)

    @api.onchange('orientation')
    def onchange_orientation(self):
        """Set background field to false for hiding option to customize login
           page background """
        if self.orientation == 'default':
            self.background = False
