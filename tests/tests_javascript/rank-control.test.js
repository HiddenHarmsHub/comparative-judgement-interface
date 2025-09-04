/**
 * @jest-environment jsdom
 */
/* global describe, require, test, expect */

const rankControl = require('../../comparison_interface/static/js/src/rank-control.js');

describe('unit tests for standalone functions in rank-control.js', () => {

  /* tests for the functions that don't call other functions */


  test('both items have aria-selected set to false when resetAriaChecked is called', () => {
    document.body.innerHTML = '<img id="image-1" aria-checked="true"/><img id="image-2" aria-checked="true"/>';
    const item1 = document.getElementById('image-1');
    const item2 = document.getElementById('image-2');
    rankControl.resetAriaChecked(item1, item2);
    expect (document.getElementById('image-1').getAttribute('aria-checked')).toBe('false');
    expect (document.getElementById('image-2').getAttribute('aria-checked')).toBe('false');
  });

  test('selected_item_id value is set correctly', () => {
    document.body.innerHTML = '<input type="hidden" id="selected_item_id" value=""/>';
    rankControl.setSelectedItem('2');
    expect(document.getElementById('selected_item_id').value).toBe('2');
  });

  test('the "selected" visual hint is added correctly', () => {
    document.body.innerHTML = '<input type="hidden" id="selected_item_indicator" value="HIGHER"/>' +
                              '<input type="hidden" id="tied_items_indicator" value="EQUAL"/>' +
                              '<input type="hidden" id="skipped_items_indicator" value="SKIPPED"/>' +
                              '<img id="left-item"/><img id="right-item"/>';
    rankControl.addVisualHint('selected-item', document.getElementById('left-item'), 'selected');
    const expectedHtml = '<input type="hidden" id="selected_item_indicator" value="HIGHER">' +
                         '<input type="hidden" id="tied_items_indicator" value="EQUAL">' +
                         '<input type="hidden" id="skipped_items_indicator" value="SKIPPED">' +
                         '<img id="left-item" class="selected-item">' +
                         '<div class="selected-hint" aria-hidden="true" style="pointer-events:none;">' +
                         '<span class="fs-1 fw-bold bg-white p-1 border border-success text-success">HIGHER</span>' +
                         '</div>' + 
                         '<img id="right-item">';
    expect(document.body.innerHTML).toBe(expectedHtml);
  });

  test('the "tied" visual hint is added correctly', () => {
    /* The function being tested here adds the hint to a single item at a time
    It is called twice for the tied case, once for each image. */
    document.body.innerHTML = '<input type="hidden" id="selected_item_indicator" value="HIGHER"/>' +
                              '<input type="hidden" id="tied_items_indicator" value="EQUAL"/>' +
                              '<input type="hidden" id="skipped_items_indicator" value="SKIPPED"/>' +
                              '<img id="left-item"/><img id="right-item"/>';
    rankControl.addVisualHint('selection-tied', document.getElementById('left-item'), 'tied');
    rankControl.addVisualHint('selection-tied', document.getElementById('right-item'), 'tied');
    const expectedHtml = '<input type="hidden" id="selected_item_indicator" value="HIGHER">' +
                          '<input type="hidden" id="tied_items_indicator" value="EQUAL">' +
                          '<input type="hidden" id="skipped_items_indicator" value="SKIPPED">' +
                          '<img id="left-item" class="selection-tied">' +
                          '<div class="selected-hint" aria-hidden="true" style="pointer-events:none;">' +
                          '<span class="fs-1 fw-bold bg-white p-1 border border-primary text-primary">EQUAL</span>' +
                          '</div>' + 
                          '<img id="right-item" class="selection-tied">' +
                          '<div class="selected-hint" aria-hidden="true" style="pointer-events:none;">' +
                          '<span class="fs-1 fw-bold bg-white p-1 border border-primary text-primary">EQUAL</span>' +
                          '</div>';
    expect(document.body.innerHTML).toBe(expectedHtml);
  });

  test('the "skipped" visual hint is added correctly', () => {
    /* The function being tested here adds the hint to a single item at a time
    It is called twice for the skipped case, once for each image. */
    document.body.innerHTML = '<input type="hidden" id="selected_item_indicator" value="HIGHER"/>' +
                              '<input type="hidden" id="tied_items_indicator" value="EQUAL"/>' +
                              '<input type="hidden" id="skipped_items_indicator" value="SKIPPED"/>' +
                              '<img id="left-item"/><img id="right-item"/>';
    rankControl.addVisualHint('selection-skipped', document.getElementById('left-item'), 'skipped');
    rankControl.addVisualHint('selection-skipped', document.getElementById('right-item'), 'skipped');
    const expectedHtml = '<input type="hidden" id="selected_item_indicator" value="HIGHER">' +
                          '<input type="hidden" id="tied_items_indicator" value="EQUAL">' +
                          '<input type="hidden" id="skipped_items_indicator" value="SKIPPED">' +
                          '<img id="left-item" class="selection-skipped">' +
                          '<div class="selected-hint" aria-hidden="true" style="pointer-events:none;">' +
                          '<span class="fs-1 fw-bold bg-white p-1 border border-black">SKIPPED</span>' +
                          '</div>' + 
                          '<img id="right-item" class="selection-skipped">' +
                          '<div class="selected-hint" aria-hidden="true" style="pointer-events:none;">' +
                          '<span class="fs-1 fw-bold bg-white p-1 border border-black">SKIPPED</span>' +
                          '</div>';
    expect(document.body.innerHTML).toBe(expectedHtml);

  });

  test('the visual hint is removed correctly', () => {
    document.body.innerHTML = '<input type="hidden" id="selected_item_indicator" value="HIGHER">' +
                              '<input type="hidden" id="tied_items_indicator" value="EQUAL">' +
                              '<input type="hidden" id="skipped_items_indicator" value="SKIPPED">' +
                              '<img id="left-item" class="selection-skipped">' +
                              '<div class="selected-hint" style="pointer-events:none;">' +
                              '<span class="fs-1 fw-bold bg-white p-1 border border-black">SKIPPED</span>' +
                              '</div>' + 
                              '<img id="right-item" class="selection-skipped">' +
                              '<div class="selected-hint" style="pointer-events:none;">' +
                              '<span class="fs-1 fw-bold bg-white p-1 border border-black">SKIPPED</span>' +
                              '</div>';
    rankControl.cleanVisualHint(
      'selection-skipped',
      document.getElementById('left-item'),
      document.getElementById('right-item')
    );
    const expectedHtml = '<input type="hidden" id="selected_item_indicator" value="HIGHER">' +
                         '<input type="hidden" id="tied_items_indicator" value="EQUAL">' +
                         '<input type="hidden" id="skipped_items_indicator" value="SKIPPED">' +
                         '<img id="left-item" class=""><img id="right-item" class="">';
    expect(document.body.innerHTML).toBe(expectedHtml);
  });

})

describe('tests for hintItem', () => {

  /* ideally the functions called by hintItem would be mocked in the following tests and just the function calls tested
  however mocking from the same module is not straight forward in jest using cjs. Switching to ES6 would probably
  make it possible but I don't want to break the accessibility tests. */

  /* The individual function tests  have already tested the html so these tests just going to pick out a few things
  here that determine if the right functions were called, they also check that the correct aria-cecked value is set */

  test('hintItem makes the right decision when a single item is clicked', () => {
    /* start with no items selected, select one item */
    document.body.innerHTML = '<input type="hidden" id="selected_item_indicator" value="HIGHER">' +
                              '<input type="hidden" id="tied_items_indicator" value="EQUAL">' +
                              '<input type="hidden" id="skipped_items_indicator" value="SKIPPED">' +
                              '<input type="hidden" id="selected_item_id">' +
                              '<input type="hidden" id="item_1_id" value="1"/>' +
                              '<input type="hidden" id="item_2_id" value="2"/>' +
                              '<input type="hidden" id="allow-ties" value="true"/>' +
                              '<img id="left-item" class="left-item" aria-checked="false"/>' +
                              '<img id="right-item" class="right-item" aria-checked="false"/>';
    const clickedItem = $('#left-item');
    rankControl.hintItem(clickedItem);
    expect(document.getElementById('selected_item_id').value).toBe('1');
    expect(document.getElementsByClassName('selected-item').length).toBe(1);
    expect(document.getElementsByClassName('selection-tied').length).toBe(0);
    expect(document.getElementsByClassName('selection-skipped').length).toBe(0);
    expect(document.getElementsByClassName('selected-hint').length).toBe(1);
    expect($('#left-item').attr('aria-checked')).toBe('true');
    expect($('#right-item').attr('aria-checked')).toBe('false');
  });

  test('hintItem makes the right decision when a single item is clicked and one is already selected (ties allowed)', () => {
    /* start with one item selected, select the second item */
    document.body.innerHTML = '<input type="hidden" id="selected_item_indicator" value="HIGHER">' +
                              '<input type="hidden" id="tied_items_indicator" value="EQUAL">' +
                              '<input type="hidden" id="skipped_items_indicator" value="SKIPPED">' +
                              '<input type="hidden" id="selected_item_id">' +
                              '<input type="hidden" id="item_1_id" value="1"/>' +
                              '<input type="hidden" id="allow-ties" value="true"/>' +
                              '<div class="selected-hint" style="pointer-events:none;">' +
                              '<span class="fs-1 fw-bold bg-white p-1 border border-success text-success">HIGHER</span>' +
                              '</div>' + 
                              '<input type="hidden" id="item_2_id" value="2"/>' +
                              '<img id="left-item" class="left-item selected-item" aria-checked="true"/>' +
                              '<img id="right-item" class="right-item" aria-checked="false"/>';
    const clickedItem = $('#right-item');
    rankControl.hintItem(clickedItem);
    expect(document.getElementById('selected_item_id').value).toBe('');
    expect(document.getElementsByClassName('selected-item').length).toBe(0);
    expect(document.getElementsByClassName('selection-tied').length).toBe(2);
    expect(document.getElementsByClassName('selection-skipped').length).toBe(0);
    expect(document.getElementsByClassName('selected-hint').length).toBe(2);
    expect($('#left-item').attr('aria-checked')).toBe('true');
    expect($('#right-item').attr('aria-checked')).toBe('true');
  });

  test('hintItem makes the right decision when a single item is clicked and one is already selected (no ties allowed)', () => {
    /* start with one item selected, select the second item */
    document.body.innerHTML = '<input type="hidden" id="selected_item_indicator" value="HIGHER">' +
                              '<input type="hidden" id="tied_items_indicator" value="EQUAL">' +
                              '<input type="hidden" id="skipped_items_indicator" value="SKIPPED">' +
                              '<input type="hidden" id="selected_item_id">' +
                              '<input type="hidden" id="item_1_id" value="1"/>' +
                              '<input type="hidden" id="allow-ties" value="false"/>' +
                              '<div class="selected-hint" style="pointer-events:none;">' +
                              '<span class="fs-1 fw-bold bg-white p-1 border border-success text-success">HIGHER</span>' +
                              '</div>' + 
                              '<input type="hidden" id="item_2_id" value="2"/>' +
                              '<img id="left-item" class="left-item selected-item" aria-checked="true"/>' +
                              '<img id="right-item" class="right-item" aria-checked="false"/>';
    const clickedItem = $('#right-item');
    rankControl.hintItem(clickedItem);
    expect(document.getElementById('selected_item_id').value).toBe('2');
    expect(document.getElementsByClassName('selected-item').length).toBe(1);
    expect(document.getElementsByClassName('selection-tied').length).toBe(0);
    expect(document.getElementsByClassName('selection-skipped').length).toBe(0);
    expect(document.getElementsByClassName('selected-hint').length).toBe(1);
    expect($('#left-item').attr('aria-checked')).toBe('false');
    expect($('#right-item').attr('aria-checked')).toBe('true');
  });

  test('hintItem makes the right decision when a single item is clicked and both are already selected', () => {
    /* start with both items selected, right-item is deselected, left becomes highest */
    document.body.innerHTML = '<input type="hidden" id="selected_item_indicator" value="HIGHER">' +
                              '<input type="hidden" id="tied_items_indicator" value="EQUAL">' +
                              '<input type="hidden" id="skipped_items_indicator" value="SKIPPED">' +
                              '<input type="hidden" id="selected_item_id">' +
                              '<input type="hidden" id="item_1_id" value="1"/>' +
                              '<input type="hidden" id="item_2_id" value="2"/>' +
                              '<input type="hidden" id="allow-ties" value="true"/>' +
                              '<img id="left-item" class="left-item selection-tied" aria-checked="true"/>' +
                              '<div class="selected-hint" style="pointer-events:none;">' +
                              '<span class="fs-1 fw-bold bg-white p-1 border border-primary text-primary">EQUAL</span>' +
                              '</div>' + 
                              '<img id="right-item" class="right-item selection-tied" aria-checked="true"/>' +
                              '<div class="selected-hint" style="pointer-events:none;">' +
                              '<span class="fs-1 fw-bold bg-white p-1 border border-primary text-primary">EQUAL</span>' +
                              '</div>';
    const clickedItem = $('#right-item');
    rankControl.hintItem(clickedItem);
    expect(document.getElementById('selected_item_id').value).toBe('1');
    expect(document.getElementsByClassName('selected-item').length).toBe(1);
    expect(document.getElementsByClassName('selection-tied').length).toBe(0);
    expect(document.getElementsByClassName('selection-skipped').length).toBe(0);
    expect(document.getElementsByClassName('selected-hint').length).toBe(1);
    expect($('#left-item').attr('aria-checked')).toBe('true');
    expect($('#right-item').attr('aria-checked')).toBe('false');
  });

  test('hintItem makes the right decision when the only selected item is deselected', () => {
    /* start with one item selected, that item is deselected */
    document.body.innerHTML = '<input type="hidden" id="selected_item_indicator" value="HIGHER">' +
                              '<input type="hidden" id="tied_items_indicator" value="EQUAL">' +
                              '<input type="hidden" id="skipped_items_indicator" value="SKIPPED">' +
                              '<input type="hidden" id="selected_item_id">' +
                              '<input type="hidden" id="item_1_id" value="1"/>' +
                              '<input type="hidden" id="allow-ties" value="true"/>' +
                              '<div class="selected-hint" style="pointer-events:none;">' +
                              '<span class="fs-1 fw-bold bg-white p-1 border border-success text-success">HIGHER</span>' +
                              '</div>' + 
                              '<input type="hidden" id="item_2_id" value="2"/>' +
                              '<img id="left-item" class="left-item selected-item" aria-checked="true"/>' +
                              '<img id="right-item" class="right-item" aria-checked="false"/>';
    const clickedItem = $('#left-item');
    rankControl.hintItem(clickedItem);
    expect(document.getElementById('selected_item_id').value).toBe('');
    expect(document.getElementsByClassName('selected-item').length).toBe(0);
    expect(document.getElementsByClassName('selection-tied').length).toBe(0);
    expect(document.getElementsByClassName('selection-skipped').length).toBe(0);
    expect(document.getElementsByClassName('selected-hint').length).toBe(0);
    expect($('#left-item').attr('aria-checked')).toBe('false');
    expect($('#right-item').attr('aria-checked')).toBe('false');
  });

})
