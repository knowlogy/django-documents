from django.dispatch import Signal

aspect_class_prepared = Signal(providing_args=["class"])

data_pre_save = Signal(providing_args=["instance"])
data_post_save = Signal(providing_args=["instance"])

data_pre_delete = Signal(providing_args=["instance"])
data_post_delete = Signal(providing_args=["instance"])

class_prepared = Signal(providing_args=["instance"])