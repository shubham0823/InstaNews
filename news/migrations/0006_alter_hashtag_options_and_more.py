# Generated by Django 5.1.4 on 2025-01-23 22:36

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('news', '0005_hashtag_alter_news_options_news_tagged_users_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='hashtag',
            options={'ordering': ['-total_count']},
        ),
        migrations.RenameField(
            model_name='hashtag',
            old_name='count',
            new_name='total_count',
        ),
    ]
