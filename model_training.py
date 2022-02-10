import torch.optim as optim
from dotenv import load_dotenv

from NLI_hyponomy_analysis.data_pipeline import embeddings_library as embed
from NLI_hyponomy_analysis.data_pipeline.NLI_data_handling import SNLI_DataLoader_Unclean, SNLI_DataLoader_Processed
from NLI_hyponomy_analysis.data_pipeline.NLI_data_handling import SNLI_DataLoader_POS_Processed
from model_library import HyperParams
from models import NeuralNetwork, StaticEntailmentNet, EntailmentTransformer
from NLI_hyponomy_analysis.data_pipeline.hyponyms import DenseHyponymMatrices


def main():
    load_dotenv()  # Path to the glove data directory -> HOME="..."

    train_path = "data/snli_1.0/snli_1.0_train.jsonl"
    validation_path = "data/snli_1.0/snli_1.0_dev.jsonl"
    test_path = "data/snli_1.0/snli_1.0_test.jsonl"

    train_small_path = "data/snli_small/snli_small1_train.jsonl"
    validation_small_path = "data/snli_small/snli_small1_dev.jsonl"

    train_loader = SNLI_DataLoader_POS_Processed(train_path)

    validation_loader = SNLI_DataLoader_POS_Processed(validation_path)

    word_vectors_0 = embed.GloveEmbedding('twitter', d_emb=25, show_progress=True, default='zero')
    word_vectors_0.load_memory()
    embed.remove_all_non_unique(word_vectors_0, train_loader.unique_words)

    word_vectors = DenseHyponymMatrices("data/hyponyms/dm-25d-glove-wn_train_lemma_pos.json")
    word_vectors.remove_all_except(train_loader.unique_words)
    word_vectors.flatten()
    word_vectors.generate_missing_vectors(train_loader.unique_words, word_vectors_0)

    params = HyperParams(heads=5, learning_rate=0.5, dropout=0.3, optimizer=optim.Adadelta,
                         patience=5, early_stopping_mode="minimum")

    mike_net = StaticEntailmentNet(word_vectors, train_loader,
                                   file_path='data/models/nn/hyponym_full_model1.pth',
                                   hyper_parameters=params, classifier_model=NeuralNetwork,
                                   validation_data_loader=validation_loader)

    mike_net.count_parameters()

    mike_net.train(epochs=100, batch_size=1000, print_every=1)
    mike_net.plot_loss()
    mike_net.plot_accuracy()
    # mike_net.test(validation_loader)


if __name__ == '__main__':
    main()
