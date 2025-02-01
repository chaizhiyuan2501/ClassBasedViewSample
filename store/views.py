from django.shortcuts import render,redirect,get_object_or_404
from django.views.generic.base import (
    View,TemplateView,RedirectView
)
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView
from django.views.generic.edit import (
    CreateView,UpdateView,DeleteView,
    FormView
)
from datetime import datetime
from . import forms
from .models import Books,Pictures
from django.urls import reverse_lazy
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib import messages


import logging
from django.http import Http404

application_logger = logging.getLogger("application-logger")
error_logger = logging.getLogger("error-logger")


class IndexView(View):
    # テンプレートに表示
    def get(self, request, *args, **kwargs):
        book_form = forms.BookForm()
        return render(request, 'index.html',context={
            "book_form":book_form,
        })
    # データベースに送信
    def post(self, request, *args, **kwargs):
        book_form = forms.BookForm(request.POST or None)
        if book_form.is_valid():
            book_form.save()
        return render(request, 'index.html',context={
            "book_form":book_form,
        })

class HomeView(TemplateView):
    template_name="home.html"
    
    application_logger.debug("Home画面を表示します")
    
    def get_context_data(self,**kwargs):
        context = super().get_context_data(**kwargs)

        if kwargs.get("name") =="あああ":
            # error_logger.error("この名前は利用できません")
            raise Http404("この名前は仕様できません")

        context["name"] = kwargs.get("name")
        context["time"] = datetime.now()
        return context

class BookDetailView(DetailView):
    model = Books
    template_name="book.html"
    
    def get_context_data(self,**kwargs):
        context = super().get_context_data(**kwargs)
        print(context)
        context["form"] = forms.BookForm()
        return context
    

class BookListView(ListView):
    model = Books
    template_name="book_list.html"
    
    def get_queryset(self):
        qs = super(BookListView,self).get_queryset()
        if "name" in self.kwargs:
            qs = qs.filter(name__startswith=self.kwargs["name"]) # 絞り込む
        qs = qs.order_by("price")  # リストの要素を逆順にする
        print(qs)
        return qs


class BookCreateView(CreateView):
    model = Books
    fields = ["name","description","price"]
    template_name = "add_book.html"
    # success_url = reverse_lazy("store:list_books")
    # formの送信時の処理をカスタマイズする
    def form_valid(self, form):
        form.instance.create_at = datetime.now()
        form.instance.update_at = datetime.now()
        return super(BookCreateView,self).form_valid(form)
    
    def get_initial(self, **kwargs):
        initial = super(BookCreateView, self).get_initial(**kwargs)
        initial["name"] = "sample"
        return initial
    


class BookUpdateView(SuccessMessageMixin,UpdateView):
    model = Books
    template_name = "update_book.html"
    form_class =forms.BookUpdateForm
    success_message = "更新に成功した"

    def get_success_url(self):
        print(self.object)
        return reverse_lazy("store:edit_book",kwargs={'pk': self.object.id})

    def get_success_message(self,cleaned_data):
        print(cleaned_data)
        return cleaned_data.get("name") + "更新しました"
    
    def get_context_data(self,**kwargs):
        context = super().get_context_data(**kwargs)
        picture_form = forms.PictureUploadForm()
        pictures = Pictures.objects.filter_by_book(book=self.object)
        context["pictures"] = pictures
        context["picture_form"] = picture_form
        return context
    
    def post(self,request,*args,**kwargs):
        #画像をアップロードする処理
        picture_form = forms.PictureUploadForm(request.POST or None,request.FILES or None)
        if picture_form.is_valid() and request.FILES:
            book = self.get_object() # 更新中のどのBookがどのBookかを取得
            picture_form.save(book=book)
        return super(BookUpdateView,self).post(request,*args,**kwargs)


class BookDeleteView(DeleteView):
    model = Books
    template_name = "delete_book.html"
    success_url = reverse_lazy("store:list_books")
    

class BookFormView(FormView):
    template_name = "form_book.html"
    form_class =forms.BookForm
    success_url = reverse_lazy("store:list_books")
    
    # Formの初期値
    def get_initial(self):
        initial = super(BookFormView, self).get_initial()
        initial["name"] = "form sample"
        return initial

    # フォームの情報をデータに保存
    def form_valid(self, form):
        if form.is_valid():
            form.save()
        return super(BookFormView,self).form_valid(form)


class BookRedirectView(RedirectView):
    url = "http://www.yahoo.co.jp"
    
    # 動的に遷移先を変更する
    def get_redirect_url(self,*args, **kwargs):
        # 最初の要素に遷移する
        book = Books.objects.first()
        # 指定した番号のページに遷移する
        if "pk" in kwargs:
            return reverse_lazy('store:detail_book',kwargs={'pk':kwargs['pk']})

        return reverse_lazy("store:edit_book",kwargs={"pk":book.pk})

def delete_picture(request,pk):
    picture = get_object_or_404(Pictures,pk=pk)
    picture.delete()
    # データベースの画像ファイルを削除する
    # import os
    # if os.path.isfile(picture.picture.path):
    #     os.remove(picture.picture.path)

    messages.success(request,"画像を削除しました")
    return redirect("store:edit_book",pk=picture.book.id)