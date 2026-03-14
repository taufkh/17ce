// odoo.define('website_blog.s_latest_posts_editor', function (require) {
// 'use strict';

// var sOptions = require('web_editor.snippets.options');
// var wUtils = require('website.utils');

// sOptions.registry.js_get_posts_selectBlog = sOptions.Class.extend({

//     //--------------------------------------------------------------------------
//     // Private
//     //--------------------------------------------------------------------------

//     /**
//      * @override
//      */
//     _renderCustomXML: function (uiFragment) {
//         var self = this;

//         self._rpc({
//             model: 'product.brand',
//             method: 'search_read',
//             domain: [['is_mccoypublished', '=', true]],
//             }).then(brands => {
//                 const menuEl1 = uiFragment.querySelector('[name="brand_id_sel"]');
//                 if(menuEl1) {
//                     for (const brand of brands) {
//                         const el1 = document.createElement('we-button');
//                         el1.dataset.selectDataAttribute = brand.id;
//                         el1.textContent = brand.name;
//                         menuEl1.appendChild(el1);
//                     }
//                 }
                    
//             });

//         this._rpc({
//             model: 'blog.blog',
//             method: 'search_read',
//             args: [wUtils.websiteDomain(this), ['name']],
//         }).then(blogs => {
//             const menuEl = uiFragment.querySelector('[name="blog_selection"]');
//             for (const blog of blogs) {
//                 const el = document.createElement('we-button');
//                 el.dataset.selectDataAttribute = blog.id;
//                 el.textContent = blog.name;
//                 menuEl.appendChild(el);
//             }

//         });


//     },
// });

// });

odoo.define('website_blog.s_latest_posts_editor', function (require) {
'use strict';

var sOptions = require('web_editor.snippets.options');
var wUtils = require('website.utils');

sOptions.registry.js_get_posts_selectBlog = sOptions.Class.extend({

    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------

    /**
     * @override
     */
    _renderCustomXML: function (uiFragment) {
        var self = this
        var html = document.documentElement;
        return this._rpc({
            model: 'website',
            method: 'get_snippet_blog',
            args: [html.getAttribute('data-website-id') | 0],
        }).then(data => {
            var menuEl1 = uiFragment.querySelector('[name="brand_id_sel"]');
            const menuEl = uiFragment.querySelector('[name="blog_selection"]');
            var blogs = data[0]
            var brands = data[1]

            for (const blog of blogs) {
                const el = document.createElement('we-button');
                el.dataset.selectDataAttribute = blog['id'];
                el.textContent = blog['name'];
                menuEl.appendChild(el);
            }
            for (const brand of brands) {
                const el1 = document.createElement('we-button');
                el1.dataset.selectDataAttribute = brand['id'];
                el1.textContent = brand['name'];
                menuEl1.appendChild(el1);
            }


        });
    },
});
});
