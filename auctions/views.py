from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from .models import User, Listing, Category, Watchlist, Bid, Comment
from django.db.models import Max

def index(request):
    
    # exlude the items from active listings, where bids are closed
    listing=Listing.objects.exclude(bidlisting__closedbid__isnull=False)
    return render(request, "auctions/index.html", {
            "listing" : listing,  
        })


def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "auctions/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "auctions/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "auctions/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "auctions/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "auctions/register.html")

@login_required(login_url="login")
# Create new listing
def create(request):
    if request.method == "POST":
        name = request.POST["name"]
        description = request.POST["description"]
        start_bid = request.POST["start_bid"]
        image = request.FILES.get("image")
        categories = request.POST.getlist("category")
        listedby = User.objects.get(id=request.user.id)
        listing = Listing(name=name,description=description,start_bid=start_bid,image=image, listedby=listedby)
        listing.save()
        # category is M2M relationship in Listing and require add() to add it in listing.
        for cat in categories:
            listing.category.add(cat)
            listing.save()
        return render(request, "auctions/create.html", {
        "message": "New item created"    
        })
    
    else:
        # To add all availble category options in form to create new listing
        return render(request, "auctions/create.html", {
            "categories": Category.objects.all(),
              
        })

@login_required(login_url="login")
def listing(request,id):
    listing = Listing.objects.get(id = id)
    categories =Category.objects.filter(categ=id)
    user = User.objects.get(id=request.user.id)
    bid=Bid.objects.filter(listingid=id).aggregate(Max("currentbid"))
    
    # listing all active items,categories, comments, bid
    if request.method == "GET":
        return render(request, "auctions/listing.html", {
        "listing":listing,
        "categories": categories,
        "watchlist": Watchlist.objects.filter(listingid = id, user = User.objects.get(id=request.user.id)),
        "bid" : bid,
        "comment" : Comment.objects.filter(listingid=id),
        })
    # Remove watchlist   
    elif request.method == "POST" and request.POST.get("remove") == id:
        watchlist = Watchlist.objects.filter(listingid = id, user = user)
        watchlist.delete()
        return render(request, "auctions/watchlist.html", {
            "message": "Item removed from watchlist."
        })
    # Add to watchlist
    elif request.method == "POST" and request.POST.get("add") == id:
        status = True
        watchlist = Watchlist(listingid = listing , status=status, user=user)
        watchlist.save()
        return render(request, "auctions/watchlist.html", {
        "message": "Item added to watchlist."
        })
    # if user has listed the item and different than starting price, update bid if user accepts the bid and close it. 
    elif request.method == "POST" and request.POST.get("closedbid") == "closedbid":
        closedbid1 = bid["currentbid__max"]
        if closedbid1:
            bid=Bid.objects.get(listingid=id, currentbid=closedbid1)
            bid.closedbid = closedbid1
            bid.save(update_fields = ["closedbid"])
            return render(request, "auctions/closedbid.html", {
            "message1": f"You have closed the bid of US$ {bid.closedbid} for item: {bid.listingid.name}. Highest bidder is {bid.user}.",
            })
        else:
            return render(request, "auctions/closedbid.html", {
            "message1": f"You have tried to close the bid at starting bid US$ {listing.start_bid} for item: {listing.name}.",
            })
    # Add comments from all users
    elif request.method == "POST" and request.POST.get("comment"):
        if request.POST.get("comment") is not None:
            comments = request.POST.get("comment")
            comment = Comment(comments=comments, commentsby=user, listingid=listing)
            comment.save()
            return render(request, "auctions/listing.html", {
                "listing":listing,
                "categories": categories,
                "watchlist": Watchlist.objects.filter(listingid = id, user = User.objects.get(id=request.user.id)),
                "bid" : bid,
                "comment" : Comment.objects.filter(listingid=id),
                })
        else:
            return render(request, "auctions/listing.html", {
            "listing":listing,
            "categories": categories,
            "watchlist": Watchlist.objects.filter(listingid = id, user = User.objects.get(id=request.user.id)),
            "bid" : bid,
            "comment" : Comment.objects.filter(listingid=id),
            })

    # Get the bid from user, compare it and save if higher.
    elif request.method=="POST" and request.POST.get("bid") != "":
        currentbid1 = request.POST.get("bid")
        if bid["currentbid__max"] is None:
            if listing.start_bid >= float(currentbid1):
                return render(request, "auctions/listing.html", {
                "message1": "Please put valid bid greater than starting bid.",
                "listing": listing,
                "categories": categories,
                "comment" : Comment.objects.filter(listingid=id),
                })
            else: 
                bid=Bid(listingid=listing, user=user, currentbid= currentbid1, listedby = listing.listedby)
                bid.save()
                count=Bid.objects.filter(listingid=id).count()
                return render(request, "auctions/listing.html", {
                "message1":   f"{count} bid(s) so far. Your bid is current bid." ,
                "listing" : listing,
                "bid" : Bid.objects.filter(listingid=id).aggregate(Max("currentbid")),
                "categories": categories,
                "comment" : Comment.objects.filter(listingid=id),
                })
        else:
            if currentbid1 is not None and bid["currentbid__max"] < float(currentbid1):
                bid = Bid(currentbid=currentbid1, listingid=listing, user=user, listedby=listing.listedby)
                bid.save()
                count=Bid.objects.filter(listingid=id).count()
                return render(request, "auctions/listing.html", {
                    "message1":   f"{count} bid(s) so far. Your bid is current bid." ,
                    "listing" : listing,
                    "bid" : Bid.objects.filter(listingid=id).aggregate(Max("currentbid")),
                    "categories": categories,
                    "comment" : Comment.objects.filter(listingid=id),
                    })
        
            else: 
                return render(request, "auctions/listing.html", {
                "message1": "Please put valid bid greater than current bid.",
                "bid" : Bid.objects.filter(listingid=id).aggregate(Max("currentbid")),
                "listing" : listing,
                "categories": categories,
                "comment" : Comment.objects.filter(listingid=id),

                })
           
    else:
        return render(request, "auctions/listing.html", {
            "message1": "Your must place valid bid.",
            "bid" : Bid.objects.filter(listingid=id).aggregate(Max("currentbid")),
            "listing" : Listing.objects.get(id=id),
            "categories": Category.objects.filter(categ= id),
            "comment" : Comment.objects.filter(listingid=id),
        })


        
@login_required(login_url="login")
def watchlist(request):
    user= request.user.id
    listing = Listing.objects.all()
    bid=Bid.objects.filter(user=user, closedbid__isnull=False)
    
    wl = Watchlist.objects.filter(user=user).exclude(listingid_id__bidlisting__closedbid__isnull= False)
    
    if wl:
        
        return render(request, "auctions/watchlist.html",{
            "watchlist": wl,
            
        })
    else: 
        return render(request, "auctions/watchlist.html",{
            "message" : "No item in watchlist"
        })
        
@login_required(login_url="login")
def closedbid(request):
    user=request.user.id
    bid= Bid.objects.filter(user=user, closedbid__isnull=False)
    return render(request, "auctions/closedbid.html", {
        "message1" : "List of bids won by you:",
        "bidlist" : bid,
        "user" : User.objects.get(id = user),
        "listing" : Listing.objects.all(),
    })

@login_required(login_url="login")
def categories(request):
    category = Category.objects.all()
    return render(request, "auctions/categories.html", {
        "category" : category,
        })
def catlist(request,id):
    cat = Category.objects.get(id=id)
    listing = Listing.objects.filter(category=id)
    return render(request, "auctions/categories.html", {
        "listing" : listing,
        "cat" : cat,
        
        }) 
    
        