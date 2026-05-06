from .models import Post, Comments
from django.core.cache import cache

class PostService:
    '''
    Service layer — handles all business logic
    View just calls this. View doesn't touch DB directly.
    '''

    @staticmethod
    def get_user_posts(user):
        cache_key = f'user_posts_{user.id}'

        # check first cache
        cached = cache.get(cache_key)
        if cached is not None:
            return cached
        
        # Not in cache hit Db
        post = Post.objects.filter(user=user).order_by('-created_at')

        cache.set(cache_key, post, timeout=60)

        return post
        
    @staticmethod
    def create_post(user, validated_data):
        post =  Post.objects.create(
            user=user,
            title=validated_data['title'],
            content=validated_data['content']
        )
    
        # Invalid Cache when we post created
        cache_key = f'user_posts_{user.id}'
        cache.delete(cache_key)
        return post
    
    
    @staticmethod
    def get_post_by_id(pk):
        try:
            return Post.objects.get(pk=pk)
        except Post.DoesNotExist:
            return None
        

    @staticmethod
    def update_post(post,  validated_data):
        for key, value in validated_data.items():
            setattr(post, key, value)
        post.save()
        return post
    
    @staticmethod
    def delete_post(post):
        # Invalidate cache when post deleted
        cache_key = f'user_posts_{post.user.id}'
        cache.delete(cache_key)
        post.delete()



class CommentService:
    """
    Service layer for comments
    """

    @staticmethod
    def get_post_comments(post_pk):
        return Comments.objects.filter(
            post__pk=post_pk
        ).order_by('-created_at')
    
    @staticmethod
    def create_comment(user, post, validated_data):
        return Comments.objects.create(
            user=user,
            post=post,
            content=validated_data['content']

        )
    
    @staticmethod
    def delete_command(comment):
        comment.delete()
    
