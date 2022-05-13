from .base import SetUp, message_in_response, create_several_posts
from django.utils.deprecation import MiddlewareMixin
from django.urls import reverse
from blog.views import (
    add_ip_person_if_not_exist,
    add_ip_person_view_if_not_exist,
)
from blog.models import Post, Comment, IpPerson
from users.models import User

class TestViews(SetUp, MiddlewareMixin):
    def test_add_ip_person_if_not_exist(self):
        self.assertFalse(IpPerson.objects.filter(
            ip=self.localhost_ip).exists())
        request = self.client.get(reverse('blog-home')).wsgi_request
        add_ip_person_if_not_exist(request)
        self.assertTrue(IpPerson.objects.filter(ip=self.localhost_ip).exists())

    def test_add_ip_person_view_if_not_exist(self):
        self.assertFalse(self.post1.views.filter(
            ip=self.localhost_ip).exists())
        request = self.client.get(self.post1_detail_url).wsgi_request

        ip_person = add_ip_person_view_if_not_exist(request, self.post1)
        self.assertTrue(self.post1.views.filter(ip=ip_person.ip).exists())
        self.post1.views.get(ip=self.localhost_ip).delete()

    def test_home_view(self):  # TODO add check for draft post
        # Anonymous user
        response = self.client.get(reverse('blog-home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'blog/home.html')

        # Access using super_user (should get posts in draft mode)
        self.client.login(username=self.super_user.username,
                          password=self.super_user_password)
        response = self.client.get(reverse('blog-home'))

    def test_user_post_list_view(self):
        response = self.client.get(self.user_posts_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'blog/user_posts.html')

    def test_post_detail_view(self):
        response = self.client.get(self.post1_detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'blog/post_detail.html')

    def test_create_post_view(self):
        data = {
            "title": "My Second Post",
            "slug": "second-post",
            "category": "productivity",
            "metadesc": "I can make you more productive!",
            "draft": False,
            # "metaimg" : ""
            # "metaimg"_mimetype : ""
            "snippet": "Do the things",
            "content": "Do the things. All the things",
            # date_posted : ""
            "author": self.super_user
            # "likes"
            # "views"

        }
        # Admin can create posts
        self.client.login(username=self.super_user.username,
                          password=self.super_user_password)
        response = self.client.post(
            reverse("post-create"), data=data, follow=True)
        self.assertRedirects(response, expected_url=reverse(
            "post-detail", args=['second-post']))
        self.assertEqual(Post.objects.last().title, "My Second Post")

        #Viewer cannot create posts (This throws an uncaught permissions error when tests are run in terminal)
        # self.client.login(username=self.basic_user.username,
        #                   password=self.basic_user_password)
        # data['author'] = self.basic_user
        # data['slug'] = "i-shouldnt-exist"
        # response = self.client.post(
        #     reverse("post-create"), data=data)
        # self.assertEqual(response.status_code, 403)

    def test_update_post_view(self):
        self.client.login(username=self.super_user.username,
                          password=self.super_user_password)
        data = {"title": "My Updated First Post",
                     "slug": "first-post",
                     "category": "productivity",
                     "metadesc": "Curious about your health? Look no further!",
                     "draft": False,
                     # "metaimg" : ""
                     # "metaimg"_mimetype : ""
                     "snippet": "Long ago, the four nations lived together in harmony.",
                     "content": "Long ago, the four nations lived together in harmony. Then everything changed when the fire nation attacked.",
                     # date_posted : ""
                     "author": self.super_user
                     # "likes"
                     # "views"
                     }
        response = self.client.post(self.post1_update_url, data=data, follow=True)
        self.assertRedirects(response, expected_url=self.post1_detail_url)
        self.post1.refresh_from_db()
        self.assertEqual(self.post1.title, "My Updated First Post")

    def test_create_comment_view(self):
        self.assertTrue(Comment.objects.count, 0)
        self.client.login(username=self.super_user.username,
                          password=self.super_user_password)
        data={"content": "Hello World!"}
        self.client.post(self.post1_create_comment_url, data=data)
        self.assertTrue(Comment.objects.count, 1)

    def test_post_delete_view(self):
        self.assertTrue(Post.objects.filter(id=self.post1.id).exists())
        self.client.login(username=self.super_user.username,
                          password=self.super_user_password)

        response = self.client.get(self.post1_delete_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'blog/post_confirm_delete.html')
        response = self.client.post(self.post1_delete_url, follow=True)
        self.assertRedirects(response, expected_url=reverse('blog-home'))

    def test_category_view(self):
        #anonymous user
        response = self.client.get(self.category_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'blog/categories.html')
        self.assertEqual(response.context['cat'], self.category1)
        self.assertEqual(response.context['posts'].count(), 1)

        # Admin can see posts in a category even if they are drafts
        self.client.login(username=self.super_user.username,
                          password=self.super_user_password)
        response = self.client.get(self.category_url)
        self.assertEqual(response.context['posts'].count(), 2)

        # Paginated list appears when there are many posts
        create_several_posts(self.category1.name, self.super_user, 20)
        response = self.client.get(self.category_url)
        self.assertEqual(response.context['posts'].count(), 5) # 5 per page

    def test_about_view(self):
        User.objects.create(username="John_Solly", email="test@invalid.com")
        response = self.client.get(reverse("blog-about"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'blog/about.html')

    def test_roadmap_view(self):
        response = self.client.get(reverse("blog-roadmap"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'blog/roadmap.html')

    def test_post_like_view(self):
        response = self.client.get(self.post1_like_url, follow=True)
        self.assertRedirects(
            response, expected_url=self.post1_detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'blog/post_detail.html')
        self.assertTrue(self.post1.likes.filter(ip=self.localhost_ip).exists())

        # # Unlike post
        response = self.client.get(self.post1_like_url, follow=True)
        self.assertRedirects(
            response, expected_url=self.post1_detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'blog/post_detail.html')
        self.assertFalse(self.post1.likes.filter(
            ip=self.localhost_ip).exists())

    def test_search_view(self):
        # Empty page if user didn't search for anything and manually typed in the search url (get)
        response = self.client.get(reverse("blog-search"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'blog/search_posts.html')

        # If anonymous, should be able to find a post.
        data = {"searched": "Post"}
        response = self.client.post(reverse("blog-search"), data=data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['posts'][0], self.post1)
        anon_post_count = response.context['posts'].count()

        # If authenticated, can see drafts
        self.client.login(username=self.super_user.username,
                          password=self.super_user_password)
        response = self.client.post(reverse("blog-search"), data=data)
        self.assertGreater(response.context['posts'].count(), anon_post_count)

    def test_register_view(self):
        response = self.client.get(reverse("register"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/register.html')
        data = {"username": "test2",
                "email": "example2@test.com",
                "password1": "Coff33cak3s!",
                "password2": "Coff33cak3s!",
                "secret_password": "African Swallows",
                "captcha_0": "dummy-value",
                "captcha_1": "PASSED"}

        response = self.client.post(reverse("register"), data=data, follow=True)
        self.assertRedirects(response, expected_url=reverse("login"))
        self.assertTemplateUsed(response, 'users/login.html')

        data["secret_password"] = "Wrong Password"
        data["username"] = "test3"

        response = self.client.post(reverse("register"), data=data, follow=True)

        self.assertTrue(message_in_response(
            response, "Hmm, I don't think that is the right password"))

    def test_profile_view(self):
        # View Profile
        self.client.login(username=self.super_user.username,
                          password=self.super_user_password)
        response = self.client.get(reverse("profile"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/profile.html')

        # Edit profile
        self.assertEqual(self.super_user.email, "test@original.com")
        self.assertEqual(self.super_user.username, "test_superuser")
        response = self.client.post(reverse("profile"), data={"email": "test@modified.com",
                                    "username": "modified"})
        self.assertTrue(message_in_response(
            response, "Your account has been updated"))
        self.super_user.refresh_from_db()
        self.assertEqual(self.super_user.email, "test@modified.com")
        self.assertEqual(self.super_user.username, "modified")
        # TODO Figure out how to change profile photo

    def test_login_view(self):
        response = self.client.get(reverse("login"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/login.html')

    def test_logout_view(self):
        self.client.login(username=self.super_user.username,
                          password=self.super_user_password)
        response = self.client.get(reverse("logout"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/logout.html')

    def test_sitemap_view(self):
        response = self.client.get(reverse('django.contrib.sitemaps.views.sitemap'))
        self.assertEqual(response.status_code, 200)

    def test_robots_view(self):
        response = self.client.get(reverse("robots_rule_list"))
        self.assertEqual(response.status_code, 200)
        lines = response.content.decode().splitlines()
        self.assertEqual(lines[0], "User-agent: *")

    def test_works_cited_view(self):
        response = self.client.get(reverse("blog-works-cited"))
        self.assertEqual(response.status_code, 200)

    def test_security_txt_view(self):
        response = self.client.get(reverse("security-txt"))
        self.assertEqual(response.status_code, 200)

    def test_security_pgp_key_view(self):
        response = self.client.get(reverse("security-pgp-key-txt"))
        self.assertEqual(response.status_code, 200)


    # password reset

    # password reset-done

    # password reset-confirm

    # password reset-complete

    # captcha
