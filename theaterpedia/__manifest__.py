{ 'name': 'Theaterpedia Configuration',
  'summary': "Basic configuration for Theaterpedia with Crearis",
  'author': "Hans Dönitz / Theaterpedia",
  'website': "http://www.theaterpedia.org",
  'version': '16.0.1.1.0',
  'category': 'Website/Crearis',
  'license': 'LGPL-3',
  'application': False,
  'depends': ['crearis'],
  'data': [
    'data/website.csv', 
    'data/res.company.csv'
  ],
  'post_init_hook': 'post_init_hook',
}