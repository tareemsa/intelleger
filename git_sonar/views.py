from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
import requests
from .models import GitHubToken
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import GitHubToken
import requests

class GitHubCallbackView(APIView):
    def get(self, request, *args, **kwargs):
        code = request.GET.get('code')
        token_url = 'https://github.com/login/oauth/access_token'
        token_data = {
            'client_id': settings.GITHUB_CLIENT_ID,
            'client_secret': settings.GITHUB_CLIENT_SECRET,
            'code': code
        }
        headers = {'Accept': 'application/json'}
        token_response = requests.post(token_url, data=token_data, headers=headers)
        token_json = token_response.json()
        access_token = token_json.get('access_token')

        if access_token:
            # Assuming you have a way to identify the user, such as a logged-in session
            user = request.user  # Replace with your actual user retrieval logic
            GitHubToken.objects.update_or_create(user=user, defaults={'access_token': access_token})

            return Response({'message': 'GitHub authentication successful'}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Failed to retrieve access token'}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def list_repositories(request):
    user = request.user  # Replace with your actual user retrieval logic
    try:
        token = GitHubToken.objects.get(user=user).access_token
    except GitHubToken.DoesNotExist:
        return Response({'error': 'GitHub token not found'}, status=status.HTTP_400_BAD_REQUEST)

    headers = {'Authorization': f'token {token}'}
    repos_url = 'https://api.github.com/user/repos'
    response = requests.get(repos_url, headers=headers)
    repos = response.json()

    return Response(repos)
