"""Wishlist and comparison prerequisites for Part D."""

import re

import uuid

from playwright.sync_api import expect

BASE = 'https://opencart.abstracta.us/index.php?route='

PRODUCTS = {40: 'iPhone', 43: 'MacBook', 28: 'HTC Touch HD'}

def visit(page, route):
    page.goto(BASE + route, wait_until='domcontentloaded', timeout=60000)
    expect(page.locator('#content')).to_be_visible()

def register_account(page):
    """Create a dedicated synthetic account; this is prerequisite work, not Part B."""
    visit(page, 'account/register')
    email = 'a3-de-' + uuid.uuid4().hex[:18] + '@example.net'
    values = {'firstname': 'Automation', 'lastname': 'Test', 'email': email,
              'telephone': '0000000000', 'password': 'PracticeTest42!', 'confirm': 'PracticeTest42!'}
    for field, value in values.items():
        page.locator('#input-' + field).fill(value)
    page.locator('input[name=agree]').check()
    page.locator('input[type=submit]').click()
    expect(page).to_have_url(re.compile(r'route=account/success'))
    expect(page.locator('#content')).to_contain_text('Your new account has been successfully created')
    return email

def product(page, product_id):
    visit(page, f'product/product&product_id={product_id}')
    expect(page.locator('#content h1')).to_have_text(PRODUCTS[product_id])
    model = page.locator('#content li').filter(has_text='Product Code:').inner_text().split(':', 1)[1].strip()
    price_text = page.locator('#content .col-sm-4 ul.list-unstyled h2').inner_text()
    return {'id': product_id, 'name': PRODUCTS[product_id], 'model': model, 'price_text': price_text}

def wishlist_add(page, product_id):
    info = product(page, product_id)
    page.locator(f'button[onclick="wishlist.add(\'{product_id}\');"]').click()
    expect(page.locator('.alert-success')).to_be_visible()
    return info

def wishlist_ids(page):
    visit(page, 'account/wishlist')
    return page.locator('#content tbody tr td:nth-child(2) a').evaluate_all(
        '(es)=>es.map(e=>Number(new URL(e.href).searchParams.get("product_id"))).sort((a,b)=>a-b)')

def compare_names(page):
    visit(page, 'product/compare')
    return page.locator('#content table tbody').first.locator('tr').first.locator('td a strong').all_text_contents()
