# -*- coding: utf-8 -*-
import logging
import re

from django.shortcuts import render_to_response, get_object_or_404
from django.core.urlresolvers import reverse
from django.forms.models import save_instance
from django.http import (HttpResponse, HttpResponseRedirect,
                         HttpResponseNotAllowed)
from django.views.decorators.csrf import csrf_protect
from django.template import RequestContext
from django.contrib.sessions.models import Session
from django.core.exceptions import ObjectDoesNotExist

from pyPdf import PdfFileWriter, PdfFileReader

from pdfserver.models import Upload
from pdfserver.forms import UploadForm

@csrf_protect
def main(request):
    # session might not exist yet
    try:
        session = Session.objects.get(session_key=request.session.session_key)
        files = Upload.objects.filter(session=session)
    except ObjectDoesNotExist:
        files = []

    return render_to_response('main.html',
                              {
                               'uploads': files,
                               'form': UploadForm(),
                              },
                              context_instance=RequestContext(request))

def upload_file(request):
    if request.method == 'POST':
        form = UploadForm(request.POST, request.FILES)

        if form.is_valid():
            logging.info("Upload form is valid: %s" % form)
            upload = Upload()

            # link to session
            session = Session.objects.get(
                session_key=request.session.session_key)
            upload.session = session

            file_obj = form.files['file']
            # save original name
            upload.filename = file_obj.name

            # save pdf page count
            try:
                file_obj.open('r')
                pdf_obj = PdfFileReader(file_obj)
                upload.page_count = pdf_obj.getNumPages()
                file_obj.close()
            except Exception, e:
                pass

            save_instance(form, upload)

            logging.info("Saved upload: %s" % upload)
        else:
            logging.error("invalid form: %s" % form)
            logging.error("form errors: %s" % form.errors)

    return HttpResponseRedirect(reverse('uploads'))

#@csrf_protect
#def confirm_delete(request):
    #if request.method != 'POST':
        #return HttpResponseNotAllowed(['POST'])

    #upload = get_object_or_404(Upload, id=request.POST.get('id', None))
    #return render_to_response('confirm_delete.html', {'upload': upload},
                              #RequestContext(request))

@csrf_protect
def delete(request):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    if request.POST.get('delete', False):
        upload = get_object_or_404(Upload, id=request.POST.get('id', None))

        upload.file.delete()
        upload.delete()

    return HttpResponseRedirect(reverse('uploads'))

@csrf_protect
def confirm_delete_all(request):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    session = Session.objects.get(session_key=request.session.session_key)
    files = Upload.objects.filter(session=session)
    return render_to_response('confirm_delete_all.html', {'uploads': files},
                              RequestContext(request))

@csrf_protect
def delete_all(request):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    if request.POST.get('delete', False):
        session = Session.objects.get(session_key=request.session.session_key)
        files = Upload.objects.filter(session=session)

        for upload in files:
            upload.file.delete()
            upload.delete()

    return HttpResponseRedirect(reverse('uploads'))

@csrf_protect
def combine_pdfs(request):

    def order_files(files, order):
        order = map(int, re.findall(r'\d+', order))

        if (not order or len(files) != len(order) or min(order) != 1 or
            max(order) != len(files)):
            order = range(1, len(files)+1)

        return ((idx, files[idx-1]) for idx in order)

    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    output = PdfFileWriter()

    session = Session.objects.get(session_key=request.session.session_key)
    files = Upload.objects.filter(session=session)

    # Get pdf objects and arrange in the user selected order, then parse ranges
    order = request.POST.get('order', "")
    for item_idx, file_obj in order_files(files, order):
        file_obj.file.open('r')
        pdf_obj = PdfFileReader(file_obj.file)
        page_count = pdf_obj.getNumPages()

        pages = request.POST.get('pages_%d' % item_idx, "")
        page_ranges = []
        if pages:
            # TODO report errorneous inputs to user, Javascript?
            ranges = re.findall(r'\d+\s*-\s*\d*|\d*\s*-\s*\d+|\d+', pages)
            for pages in ranges:
                match_obj = re.match(r'^(\d*)\s*-\s*(\d*)$', pages)
                if match_obj:
                    from_page, to_page = match_obj.groups()
                    # TODO report errorneous input to user, Javascript?
                    if from_page:
                        from_page_idx = max(int(from_page)-1, 0)
                    else:
                        from_page_idx = 0
                    if to_page:
                        to_page_idx = min(int(to_page), page_count)
                    else:
                        to_page_idx = page_count

                    page_ranges.append(range(from_page_idx, to_page_idx))
                else:
                    page_idx = int(pages)-1
                    # TODO report errorneous input to user, Javascript?
                    if page_idx >= 0 and page_idx < page_count:
                        page_ranges.append([page_idx])
        else:
            page_ranges = [range(pdf_obj.getNumPages())]

        # Extract pages from PDF
        for page_range in page_ranges:
            for page_idx in page_range:
                page = pdf_obj.getPage(page_idx)
                output.addPage(page)

    # TODO get proper file name
    response = HttpResponse(mimetype='application/pdf')
    response['Content-Disposition'] = 'attachment; filename=combined.pdf'

    output.write(response)

    return response