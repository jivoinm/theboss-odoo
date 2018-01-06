import xmlrpclib
srv_source = 'http://frasinul.freeddns.org'
admin_user_source = 'theboss.mircea@gmail.com'
admin_password_source = '851308'
db_name_source = 'bitnami_odoo'

srv = 'http://localhost:8069'
admin_user = 'admin'
admin_password = 'admin'
db_name = 'test'

common_source = xmlrpclib.ServerProxy('%s/xmlrpc/2/common' % srv_source)
uid_source = common_source.authenticate(db_name_source, admin_user_source, admin_password_source, {})

common = xmlrpclib.ServerProxy('%s/xmlrpc/2/common' % srv)
uid = common.authenticate(db_name, admin_user, admin_password, {})

models_source = xmlrpclib.ServerProxy('{}/xmlrpc/2/object'.format(srv_source))
models_dest = xmlrpclib.ServerProxy('{}/xmlrpc/2/object'.format(srv))

def merge(module, fields=None):
    query_fields = {'fields': fields} if fields else {}
    listing_fields = {'allfields': fields} if fields else {}

    source_records = models_source.execute_kw(db_name_source, uid_source, admin_password_source, module, 'search_read', [[]], query_fields)
    #create_records = []
    for record in source_records:
        try:
            existing_records = models_dest.execute_kw(db_name, uid, admin_password, module, 'search_count', [[['name', '=', record['name']]]])
            if existing_records == 0:
                fields = models_dest.execute_kw(db_name, uid, admin_password, module, 'fields_get', [], listing_fields)
                create_record = {}
                for field in record:
                    if field.endswith('_id'):
                        relation_model = fields[field]['relation']
                        record_name = record[field][1]
                        relation = existing_records = models_dest.execute_kw(db_name, uid, admin_password, relation_model, 'search', [[['name', '=', record_name]]])
                        create_record[field] = relation[0]
                    elif field != "id":
                        create_record[field] = record[field]
                print("create ", create_record)
                #create_records.append(create_record)
                models_dest.execute_kw(db_name, uid, admin_password, module, 'create', [create_record])            
            else:
                print("record {0}, already exist".format(record['name']))
        except Exception as identifier:
            print("Error creating record {0}".format(identifier))
    
#merge brands
merge('res.user')
merge('fleet.vehicle.model.brand')
merge('fleet.vehicle.model', ['name', 'brand_id'])
merge('fleet.vehicle', ['name', 'brand_id'])
