"""T012: compare attributes, deduplicate and remove entries."""
import pytest
from playwright.sync_api import expect
from ui_helpers import product, compare_names


def add_after_product_load(page, product_id):
    # The product review request must finish before the session-changing action.
    with page.expect_response(lambda response: 'route=product/product/review' in response.url) as review:
        info = product(page, product_id)
    review.value.finished()
    page.locator(f'button[onclick="compare.add(\'{product_id}\');"]').click()
    expect(page.locator('.alert-success')).to_contain_text(info['name'])
    return info


@pytest.mark.parametrize('scenario', ['T012-S01', 'T012-S02', 'T012-S03'])
def test_product_comparison(page, record, scenario):
    first = add_after_product_load(page, 40)
    # Read the current product attributes instead of fixing today's price in code.
    second = add_after_product_load(page, 40 if scenario.endswith('02') else 43)
    record['input'] = {'add_product_ids': [40, second['id']], 'remove_product_id': 40 if scenario.endswith('03') else None}
    names = compare_names(page)
    record['observations'] = {'comparison_names': names, 'reference_products': [first, second]}
    if scenario.endswith('02'):
        assert names == ['iPhone']
    else:
        assert len(names) == 2 and set(names) == {'iPhone', 'MacBook'}
        table = page.locator('#content table')
        for info in [first, second]:
            # Associate each model and price with its own named product column.
            column = names.index(info['name']) + 1
            model_row = table.locator('tr').filter(has=page.get_by_role('cell', name='Model', exact=True))
            price_row = table.locator('tr').filter(has=page.get_by_role('cell', name='Price', exact=True))
            expect(model_row.locator('td').nth(column)).to_have_text(info['model'])
            expect(price_row.locator('td').nth(column)).to_contain_text(info['price_text'])
        if scenario.endswith('03'):
            # Removing one comparison column must retain the other product.
            page.locator('#content a[href*="remove=40"]').click()
            names = compare_names(page)
            assert names == ['MacBook']
    record['observations'] = {'comparison_names': names, 'reference_products': [first, second]}
