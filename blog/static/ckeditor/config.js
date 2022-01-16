/**
 * @license Copyright (c) 2003-2016, CKSource - Frederico Knabben. All rights reserved.
 * For licensing, see LICENSE.md or http://ckeditor.com/license
 */

CKEDITOR.editorConfig = function( config ) {
	// Define changes to default configuration here. For example:
	// config.language = 'fr';
	// config.uiColor = '#AADC6E';
	config.language = 'zh-cn';
    config.toolbar = 'Basic';
    config.toolbar = 'Full';
    config.width = 800;
    config.height = 400;
    config.toolbar_Full = [
    ['Source', '-', 'Save', 'NewPage', 'Preview', '-', 'Templates'],
    ['Cut', 'Copy', 'Paste', 'PasteText', 'PasteFromWord', '-', 'Print', ], 
    //['Undo', 'Redo', '-', 'Find', 'Replace', '-', 'SelectAll', 'RemoveFormat'],
    ['Form', 'Checkbox', 'Radio', 'TextField', 'Textarea', 'Select', 'Button', 'ImageButton', 'HiddenField'],
    '/',
    ['Bold', 'Italic', 'Underline', 'Strike', '-', 'Subscript', 'Superscript'],
    ['NumberedList', 'BulletedList', '-', 'Outdent', 'Indent', 'Blockquote'],
    ['JustifyLeft', 'JustifyCenter', 'JustifyRight', 'JustifyBlock'],
    ['Link', 'Unlink', 'Anchor'],
    ['Image', 'Flash', 'Table', 'HorizontalRule', 'Smiley', 'SpecialChar', 'PageBreak'],
       '/',
    ['Styles', 'Format', 'Font', 'FontSize'],
    ['TextColor', 'BGColor'],
    //ȫ��           ��ʾ����
    ['Maximize', 'ShowBlocks','-']
    ];
    
    config.filebrowserBrowseUrl = '/static/ckfinder/ckfinder.html'; //�ϴ��ļ�ʱ��������ļ���
    config.filebrowserImageBrowseUrl = '/static/ckfinder/ckfinder.html?Type=Images'; //�ϴ�ͼƬʱ��������ļ���
    config.filebrowserFlashBrowseUrl = 'http://www.cnblogs.com/Scripts/ckfinder/ckfinder.html?Type=Flash';  //�ϴ�Flashʱ��������ļ���
    config.filebrowserUploadUrl = '/Scripts/ckfinder/core/connector/aspx/connector.aspx?command=QuickUpload&type=Files'; //�ϴ��ļ���ť(��ǩ) 
    config.filebrowserImageUploadUrl = '/uploadimage/'; //�ϴ�ͼƬ��ť(��ǩ) 
    config.filebrowserFlashUploadUrl = 'http://www.cnblogs.com/Scripts/ckfinder/core/connector/aspx/connector.aspx?command=QuickUpload&type=Flash'; //�ϴ�Flash��ť(��ǩ)
};
