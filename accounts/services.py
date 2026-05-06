from .models import Post, Comments

class PostService:
    '''
    Service layer — handles all business logic
    View just calls this. View doesn't touch DB directly.
    '''

    @staticmethod
    def get_user_posts(user):
        return Post.objects.filter(user=user).order_by('-created_at')
    
    @staticmethod
    def create_post(user, validated_data):
        return Post.objects.create(
            user=user,
            title=validated_data['title'],
            content=validated_data['content']
        )
    
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
    
