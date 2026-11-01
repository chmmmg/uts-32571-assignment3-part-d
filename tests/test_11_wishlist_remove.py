"""T011: remove a saved product without losing unrelated products."""
import pytest
from playwright.sync_api import expect
from ui_helpers import register_account, wishlist_add, wishlist_ids


@pytest.mark.parametrize('scenario', ['T011-S01', 'T011-S02', 'T011-S03'])
def test_wishlist_remove(page, record, scenario):
    source, target = {'T011-S01': ([40], 40), 'T011-S02': ([40, 43], 40), 'T011-S03': ([40, 43, 28], 43)}[scenario]
    record['input'] = {'account_email': register_account(page), 'initial_product_ids': source, 'remove_product_id': target}
    for pid in source:
        wishlist_add(page, pid)
    assert wishlist_ids(page) == sorted(source)
    page.locator(f'#content a[href*="remove={target}"]').click()
    remaining = wishlist_ids(page)
    # Check the selected ID and preserve every unrelated saved product.
    record['observations'] = {'remaining_product_ids': remaining, 'removed_product_absent': target not in remaining,
                              'visible_message': page.locator('#content').inner_text() if not remaining else None}
    assert remaining == sorted(set(source) - {target})
    if not remaining:
        # The empty-state message must describe the wishlist, not the cart.
        expect(page.locator('#content')).to_contain_text('Your wish list is empty.')
