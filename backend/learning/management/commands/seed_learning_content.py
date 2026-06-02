from learning.management.commands.seed_learning_catalog import Command as SeedLearningCatalogCommand


class Command(SeedLearningCatalogCommand):
    help = "Alias for seed_learning_catalog; seeds external learning content."
