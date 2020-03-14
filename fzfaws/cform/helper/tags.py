"""Handle tags operation"""


def get_tags(update=False):
    """get new tags for stacks during update or create

    Args:
        update: bool, display different message based on this arg
    Returns:
        A list of dict with {'Key': value, 'Value': value}
    """

    tag_list = []
    if not update:
        print('Tags help you identify your sub resources')
        print('A "Name" tag is suggested to enter at the very least')
        print('Skip enter value to stop entering for tags')
    else:
        print('Enter new tags below')
        print('Skip enter value to stop entering for new tags')
    while True:
        tag_name = input('TagName: ')
        if not tag_name:
            break
        tag_value = input('TagValue: ')
        if not tag_value:
            break
        tag_list.append({'Key': tag_name, 'Value': tag_value})
    return tag_list


def update_tags(tags):
    """update existing tags

    Args:
        tags: list, response from boto3
    Returns:
        A list of dict with {'Key': value, 'Value': value}
    """

    new_tags = []
    print(80*'-')
    print('Update tags')
    print('Skip the value to use previouse value')
    print('Enter delete in both field to remove a tag')
    for tag in tags:
        tag_key = input(f"Key({tag['Key']}): ")
        if not tag_key:
            tag_key = tag['Key']
        tag_value = input(f"Value({tag['Value']}): ")
        if not tag_value:
            tag_value = tag['Value']
        if tag_key == 'delete' and tag_value == 'delete':
            continue
        new_tags.append(
            {'Key': tag_key, 'Value': tag_value})
    return new_tags