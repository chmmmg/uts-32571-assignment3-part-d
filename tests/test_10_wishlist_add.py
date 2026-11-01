"""T010: wishlist insertion, duplicate handling and guest access."""
import re
import pytest
from playwright.sync_api import expect
from ui_helpers import register_account, wishlist_add, wishlist_ids, visit


@pytest.mark.parametrize('scenario', ['T010-S01', 'T010-S02', 'T010-S03'])
def test_wishlist_add(page, record, scenario):
    record['input'] = {'product_id': 40, 'attempts': 2 if scenario.endswith('02') else 1}
    if scenario.endswith('03'):
        # A guest must receive a login notice and cannot open the account wishlist.
        wishlist_add(page, 40)
        expect(page.locator('.alert-success')).to_contain_text('login')
        visit(page, 'account/wishlist')
        expect(page).to_have_url(re.compile(r'route=account/login'))
        expect(page.locator('#input-email')).to_be_visible()
        record['observations'] = {'guest_notice': 'login required', 'wishlist_access': 'login page'}
    else:
        record['input']['account_email'] = register_account(page)
        info = wishlist_add(page, 40)
        if scenario.endswith('02'):
            wishlist_add(page, 40)
        ids = wishlist_ids(page)
        # Reopen the saved list; a toast alone does not prove the item was saved.
        assert ids == [40], f'Unexpected wishlist IDs: {ids}'
        expect(page.locator('#content tbody')).to_contain_text(info['name'])
        expect(page.locator('#content tbody')).to_contain_text(info['model'])
        record['observations'] = {'saved_ids': ids, 'product_name': info['name'], 'model': info['model']}
