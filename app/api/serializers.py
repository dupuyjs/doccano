import requests, uuid
from django.conf import settings
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.core.files.base import ContentFile
from rest_framework import serializers
from rest_polymorphic.serializers import PolymorphicSerializer
from rest_framework.exceptions import ValidationError


from .models import Label, Project, Document, RoleMapping, Role, Conversation, ConversationItem
from .models import TextClassificationProject, SequenceLabelingProject, Seq2seqProject, ConversationsProject
from .models import DocumentAnnotation, SequenceAnnotation, Seq2seqAnnotation, ConversationItemAnnotation


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = get_user_model()
        fields = ('id', 'username', 'first_name', 'last_name', 'email', 'is_superuser')


class LabelSerializer(serializers.ModelSerializer):

    def validate(self, attrs):
        prefix_key = attrs.get('prefix_key')
        suffix_key = attrs.get('suffix_key')

        # In the case of user don't set any shortcut key.
        if prefix_key is None and suffix_key is None:
            return super().validate(attrs)

        # Don't allow shortcut key not to have a suffix key.
        if prefix_key and not suffix_key:
            raise ValidationError('Shortcut key may not have a suffix key.')

        # Don't allow to save same shortcut key when prefix_key is null.
        try:
            context = self.context['request'].parser_context
            project_id = context['kwargs']['project_id']
            label_id = context['kwargs'].get('label_id')
        except (AttributeError, KeyError):
            pass  # unit tests don't always have the correct context set up
        else:
            conflicting_labels = Label.objects.filter(
                suffix_key=suffix_key,
                prefix_key=prefix_key,
                project=project_id,
            )

            if label_id is not None:
                conflicting_labels = conflicting_labels.exclude(id=label_id)

            if conflicting_labels.exists():
                raise ValidationError('Duplicate shortcut key.')

        return super().validate(attrs)

    class Meta:
        model = Label
        fields = ('id', 'text', 'prefix_key', 'suffix_key', 'background_color', 'text_color')


class DocumentSerializer(serializers.ModelSerializer):
    annotations = serializers.SerializerMethodField()
    annotation_approver = serializers.SerializerMethodField()

    def get_annotations(self, instance):
        request = self.context.get('request')
        project = instance.project
        model = project.get_annotation_class()
        serializer = project.get_annotation_serializer()
        annotations = model.objects.filter(document=instance.id)
        if request and not project.collaborative_annotation:
            annotations = annotations.filter(user=request.user)
        serializer = serializer(annotations, many=True)
        return serializer.data

    @classmethod
    def get_annotation_approver(cls, instance):
        approver = instance.annotations_approved_by
        return approver.username if approver else None

    class Meta:
        model = Document
        fields = ('id', 'text', 'annotations', 'meta', 'annotation_approver')


class ProjectSerializer(serializers.ModelSerializer):
    current_users_role = serializers.SerializerMethodField()

    def get_current_users_role(self, instance):
        role_abstractor = {
            "is_project_admin": settings.ROLE_PROJECT_ADMIN,
            "is_annotator": settings.ROLE_ANNOTATOR,
            "is_annotation_approver": settings.ROLE_ANNOTATION_APPROVER,
        }
        queryset = RoleMapping.objects.values("role_id__name")
        if queryset:
            users_role = get_object_or_404(
                queryset, project=instance.id, user=self.context.get("request").user.id
            )
            for key, val in role_abstractor.items():
                role_abstractor[key] = users_role["role_id__name"] == val
        return role_abstractor

    class Meta:
        model = Project
        fields = ('id', 'name', 'description', 'guideline', 'users', 'current_users_role', 'project_type', 'image',
                  'updated_at', 'randomize_document_order', 'collaborative_annotation')
        read_only_fields = ('image', 'updated_at', 'current_users_role')


class TextClassificationProjectSerializer(ProjectSerializer):

    class Meta:
        model = TextClassificationProject
        fields = ('id', 'name', 'description', 'guideline', 'users', 'current_users_role', 'project_type', 'image',
                  'updated_at', 'randomize_document_order')
        read_only_fields = ('image', 'updated_at', 'users', 'current_users_role')


class SequenceLabelingProjectSerializer(ProjectSerializer):


    class Meta:
        model = SequenceLabelingProject
        fields = ('id', 'name', 'description', 'guideline', 'users', 'current_users_role', 'project_type', 'image',
                  'updated_at', 'randomize_document_order')
        read_only_fields = ('image', 'updated_at', 'users', 'current_users_role')


class Seq2seqProjectSerializer(ProjectSerializer):

    class Meta:
        model = Seq2seqProject
        fields = ('id', 'name', 'description', 'guideline', 'users', 'current_users_role', 'project_type', 'image',
                  'updated_at', 'randomize_document_order')
        read_only_fields = ('image', 'updated_at', 'users', 'current_users_role')


class ConversationsProjectSerializer(ProjectSerializer):

    class Meta:
        model = ConversationsProject
        fields = ('id', 'name', 'description', 'guideline', 'users', 'current_users_role', 'project_type', 'image',
                  'updated_at', 'randomize_document_order')
        read_only_fields = ('image', 'updated_at', 'users', 'current_users_role')


class ConversationItemSerializer(DocumentSerializer):
    startTimeInSeconds = serializers.FloatField(source='start_time')
    endTimeInSeconds = serializers.FloatField(source='end_time')
    machineTranscription = serializers.CharField(source='machine_text')
    humanTranscription = serializers.CharField(source='text')
    textValidated = serializers.BooleanField(source='text_validated', default=False)
    conversation = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = ConversationItem
        fields = ('id', 'startTimeInSeconds', 'endTimeInSeconds', 'machineTranscription', 'humanTranscription', 'textValidated', 'conversation', 'annotations', 'annotation_approver')


class DocumentPolymorphicSerializer(PolymorphicSerializer):
    model_serializer_mapping = {
        Document: DocumentSerializer,
        ConversationItem: ConversationItemSerializer,
    }


class ConversationSerializer(serializers.ModelSerializer):
    audioFileUrl = serializers.URLField(source='audio_url', write_only=True)
    metadata = serializers.JSONField(source='meta', required=False)
    sentences = ConversationItemSerializer(source='conversation_items', many=True, write_only=True)
    # @FIXME(Jeremie): Hack to be able to save file from audioUrl, a new field shoud be created
    # following this example : https://github.com/Hipo/drf-extra-fields#base64filefield
    audioFile = serializers.FileField(source='audio_file', required=False)

    def create(self, validated_data):
        # As conversation item inherit from documents we need to set the project id
        if 'conversation_items' in validated_data.keys():
            validated_data.update({'conversation_items': [
                {'project': validated_data.get('project'), **item } for item in validated_data.get('conversation_items') ]})

        many_to_many = {}
        for field_name in ['conversation_items']:
            if field_name in validated_data:
                many_to_many[field_name] = validated_data.pop(field_name)

        instance = self.Meta.model.objects.create(**validated_data)

        # Save many-to-many relationships after the instance is created.
        if many_to_many:
            for field_name, value in many_to_many.items():
                if type(value) is list:
                    for related in value:
                        field = getattr(instance, field_name)
                        field.create(**related)

        return instance

    def validate(self, data):
        if data.get('audio_url'):
            # @FIXME(Jeremie): This will probably not scale as this is sync and blocking call
            res = requests.get(data.get('audio_url'))
            if res.status_code is 200:
                data['audio_file'] = ContentFile(res.content, name=f'{uuid.uuid4()}.wav')
        return data

    class Meta:
        model = Conversation
        fields = ('id', 'audioFileUrl', 'metadata', 'audioFile', 'sentences')


class ProjectPolymorphicSerializer(PolymorphicSerializer):
    model_serializer_mapping = {
        Project: ProjectSerializer,
        TextClassificationProject: TextClassificationProjectSerializer,
        SequenceLabelingProject: SequenceLabelingProjectSerializer,
        Seq2seqProject: Seq2seqProjectSerializer,
        ConversationsProject: ConversationsProjectSerializer,
    }


class ProjectFilteredPrimaryKeyRelatedField(serializers.PrimaryKeyRelatedField):

    def get_queryset(self):
        view = self.context.get('view', None)
        request = self.context.get('request', None)
        queryset = super(ProjectFilteredPrimaryKeyRelatedField, self).get_queryset()
        if not request or not queryset or not view:
            return None
        return queryset.filter(project=view.kwargs['project_id'])


class DocumentAnnotationSerializer(serializers.ModelSerializer):
    # label = ProjectFilteredPrimaryKeyRelatedField(queryset=Label.objects.all())
    label = serializers.PrimaryKeyRelatedField(queryset=Label.objects.all())
    document = serializers.PrimaryKeyRelatedField(queryset=Document.objects.all())

    class Meta:
        model = DocumentAnnotation
        fields = ('id', 'prob', 'label', 'user', 'document')
        read_only_fields = ('user', )


class SequenceAnnotationSerializer(serializers.ModelSerializer):
    #label = ProjectFilteredPrimaryKeyRelatedField(queryset=Label.objects.all())
    label = serializers.PrimaryKeyRelatedField(queryset=Label.objects.all())
    document = serializers.PrimaryKeyRelatedField(queryset=Document.objects.all())

    class Meta:
        model = SequenceAnnotation
        fields = ('id', 'prob', 'label', 'start_offset', 'end_offset', 'user', 'document')
        read_only_fields = ('user',)


class Seq2seqAnnotationSerializer(serializers.ModelSerializer):
    document = serializers.PrimaryKeyRelatedField(queryset=Document.objects.all())

    class Meta:
        model = Seq2seqAnnotation
        fields = ('id', 'text', 'user', 'document', 'prob')
        read_only_fields = ('user',)


class ConversationItemAnnotationSerializer(DocumentAnnotationSerializer):
    
    class Meta:
        model = ConversationItemAnnotation
        fields = ('id', 'prob', 'label', 'start_offset', 'end_offset', 'user', 'document')
        read_only_fields = ('user', )


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ('id', 'name')


class RoleMappingSerializer(serializers.ModelSerializer):
    username = serializers.SerializerMethodField()
    rolename = serializers.SerializerMethodField()

    @classmethod
    def get_username(cls, instance):
        user = instance.user
        return user.username if user else None

    @classmethod
    def get_rolename(cls, instance):
        role = instance.role
        return role.name if role else None

    class Meta:
        model = RoleMapping
        fields = ('id', 'user', 'role', 'username', 'rolename')
