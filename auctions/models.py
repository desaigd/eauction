from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    pass

class Category(models.Model):
    cname = models.CharField(max_length=64, help_text='Enter a category of product (e.g. Electronics, Home Appliances)')
    def __str__(self):
       """ string for representing the model object"""
       return f"{self.cname}"

class Listing(models.Model):
    name = models.CharField(max_length=64)
    description = models.TextField()
    category = models.ManyToManyField(Category, help_text='Select category/ies for this item', related_name='categ')
    start_bid = models.FloatField()
    listedby = models.ForeignKey(User, on_delete=models.CASCADE)
    image = models.ImageField(upload_to="images/", blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"{self.name} {self.description} {self.start_bid} {self.image} {self.created} {self.category} {self.listedby} "


class Watchlist(models.Model):
    user = models.ForeignKey(User,null=True, on_delete=models.CASCADE)
    listingid = models.ForeignKey(Listing, on_delete=models.CASCADE, null=True, related_name='listingid')
    status = models.BooleanField(default=False)
    def __str__(self):
        return f"{self.user} {self.listingid} {self.status}"


class Bid(models.Model):
    currentbid = models.FloatField(null=True, blank=True)
    listingid = models.ForeignKey(Listing, on_delete = models.CASCADE, related_name='bidlisting')
    listedby = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bidlistedby')
    user = models.ForeignKey(User,null=True, on_delete=models.CASCADE,related_name='biduser')
    closedbid = models.FloatField(null=True, blank=True)
    datetime = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f" {self.closedbid}"

class Comment(models.Model):
    comments = models.TextField(blank=True)
    commentsby = models.ForeignKey(User, on_delete=models.CASCADE,related_name='commentsby')
    datetime = models.DateTimeField(auto_now_add=True)
    listingid = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name="commentslistingid")
    def __str__(self):
        return f" {self.comments}"