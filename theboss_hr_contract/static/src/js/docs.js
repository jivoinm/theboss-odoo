odoo.define('theboss_hr.hr_document', function (require) {
"use strict";

var data = require('web.data');
var Model = require('web.DataModel');
var Sidebar = require('web.Sidebar');

Sidebar.include({
    init: function () {
        var self = this;
        var ids;
        this._super.apply(this, arguments);
        var view = self.getParent();
        var result;
        if (view.fields_view && view.fields_view.type === "form") {
            ids = [];
            view.on("load_record", self, function (r) {
                ids = [r.id];
                self.add_docs(view, r.id);
            });
        }
    },
    add_docs: function (view, res_id) {
        var self = this;
        var gdoc_item = _.indexOf(_.pluck(self.items.other, 'classname'), 'oe_share_gdoc');
        if (gdoc_item !== -1) {
            self.items.other.splice(gdoc_item, 1);
        }
        if (res_id) {
            view.sidebar_eval_context().done(function (context) {
                var ds = new data.DataSet(this, 'hr.document', context);
                ds.call('get_document_template', [view.dataset.model, res_id, context]).done(function (r) {
                    if (!_.isEmpty(r)) {
                        _.each(r, function (res) {
                            var already_there = false;
                            for (var i = 0;i < self.items.other.length;i++){
                                if (self.items.other[i].classname === "oe_share_gdoc" && self.items.other[i].label.indexOf(res.name) > -1){
                                    already_there = true;
                                    break;
                                }
                            }
                            if (!already_there){
                                self.add_items('print', [{
                                        label: res.name,
                                        config_id: res.id,
                                        res_id: res_id,
                                        res_model: view.dataset.model,
                                        callback: self.on_doc,
                                        classname: 'oe_share_gdoc'
                                    },
                                ]);
                            }
                        });
                    }
                });
            });
        }
    },

    fetch: function (model, fields, domain, ctx) {
        return new Model(model).query(fields).filter(domain).context(ctx).all();
    },

    on_doc: function (doc_item) {
        var self = this;
        this.config = doc_item;
        console.log(doc_item);
        
        var self = this;                                                        
        self.rpc("/web/action/load", { 
            action_id: "theboss_hr.document_template_preview"
        })
        .done(function(result) {
            self.getParent().do_action(result, {                                                                                      
                additional_context: {                                      
                    template_id: doc_item.config_id,
                    active_id: doc_item.res_id
                },                                                         
            });                                                            
        });         
    },
});
});