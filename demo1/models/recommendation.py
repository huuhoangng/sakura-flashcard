from extensions import db

class SemanticRecommendCollection(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    targetUserID = db.Column(db.Integer, db.ForeignKey('user.id', ondelete="CASCADE"), nullable=False)
    targetCollection = db.Column(db.Integer, db.ForeignKey('collection.id', ondelete="CASCADE"), nullable=False)
    recomCollectionID = db.Column(db.Integer, db.ForeignKey('collection.id', ondelete="CASCADE"), nullable=False)
    ownerUserID = db.Column(db.Integer, db.ForeignKey('user.id', ondelete="CASCADE"), nullable=False)
    similarScore = db.Column(db.Float, nullable=False)

    target_user = db.relationship('User', foreign_keys=[targetUserID], backref=db.backref('sem_rec_cols_target', cascade="all, delete-orphan"))
    owner_user = db.relationship('User', foreign_keys=[ownerUserID], backref=db.backref('sem_rec_cols_owner', cascade="all, delete-orphan"))
    target_col = db.relationship('Collection', foreign_keys=[targetCollection], backref=db.backref('sem_rec_cols_target', cascade="all, delete-orphan"))
    recom_col = db.relationship('Collection', foreign_keys=[recomCollectionID], backref=db.backref('sem_rec_cols_recom', cascade="all, delete-orphan"))

class SemanticRecommendFlashcard(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    targetUserID = db.Column(db.Integer, db.ForeignKey('user.id', ondelete="CASCADE"), nullable=False)
    targetFlashcard = db.Column(db.Integer, db.ForeignKey('flashcard.id', ondelete="CASCADE"), nullable=False)
    recomFlashcardID = db.Column(db.Integer, db.ForeignKey('flashcard.id', ondelete="CASCADE"), nullable=False)
    ownerUserID = db.Column(db.Integer, db.ForeignKey('user.id', ondelete="CASCADE"), nullable=False)
    similarScore = db.Column(db.Float, nullable=False)

    target_user = db.relationship('User', foreign_keys=[targetUserID], backref=db.backref('sem_rec_cards_target', cascade="all, delete-orphan"))
    owner_user = db.relationship('User', foreign_keys=[ownerUserID], backref=db.backref('sem_rec_cards_owner', cascade="all, delete-orphan"))
    target_card = db.relationship('Flashcard', foreign_keys=[targetFlashcard], backref=db.backref('sem_rec_cards_target', cascade="all, delete-orphan"))
    recom_card = db.relationship('Flashcard', foreign_keys=[recomFlashcardID], backref=db.backref('sem_rec_cards_recom', cascade="all, delete-orphan"))

class DiscoverRecommendCollection(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    targetUserID = db.Column(db.Integer, db.ForeignKey('user.id', ondelete="CASCADE"), nullable=False)
    targetCollection = db.Column(db.Integer, db.ForeignKey('collection.id', ondelete="CASCADE"), nullable=False)
    recomCollectionID = db.Column(db.Integer, db.ForeignKey('collection.id', ondelete="CASCADE"), nullable=False)
    ownerUserID = db.Column(db.Integer, db.ForeignKey('user.id', ondelete="CASCADE"), nullable=False)
    discoverScore = db.Column(db.Float, nullable=False)

    target_user = db.relationship('User', foreign_keys=[targetUserID], backref=db.backref('disc_rec_cols_target', cascade="all, delete-orphan"))
    owner_user = db.relationship('User', foreign_keys=[ownerUserID], backref=db.backref('disc_rec_cols_owner', cascade="all, delete-orphan"))
    target_col = db.relationship('Collection', foreign_keys=[targetCollection], backref=db.backref('disc_rec_cols_target', cascade="all, delete-orphan"))
    recom_col = db.relationship('Collection', foreign_keys=[recomCollectionID], backref=db.backref('disc_rec_cols_recom', cascade="all, delete-orphan"))

class DiscoverRecommendFlashcard(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    targetUserID = db.Column(db.Integer, db.ForeignKey('user.id', ondelete="CASCADE"), nullable=False)
    targetFlashcard = db.Column(db.Integer, db.ForeignKey('flashcard.id', ondelete="CASCADE"), nullable=False)
    recomFlashcardID = db.Column(db.Integer, db.ForeignKey('flashcard.id', ondelete="CASCADE"), nullable=False)
    ownerUserID = db.Column(db.Integer, db.ForeignKey('user.id', ondelete="CASCADE"), nullable=False)
    discoverScore = db.Column(db.Float, nullable=False)

    target_user = db.relationship('User', foreign_keys=[targetUserID], backref=db.backref('disc_rec_cards_target', cascade="all, delete-orphan"))
    owner_user = db.relationship('User', foreign_keys=[ownerUserID], backref=db.backref('disc_rec_cards_owner', cascade="all, delete-orphan"))
    target_card = db.relationship('Flashcard', foreign_keys=[targetFlashcard], backref=db.backref('disc_rec_cards_target', cascade="all, delete-orphan"))
    recom_card = db.relationship('Flashcard', foreign_keys=[recomFlashcardID], backref=db.backref('disc_rec_cards_recom', cascade="all, delete-orphan"))

class TimeoutFlashcards(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    targetUserID = db.Column(db.Integer, db.ForeignKey('user.id', ondelete="CASCADE"), nullable=False)
    targetFlashcard = db.Column(db.Integer, db.ForeignKey('flashcard.id', ondelete="CASCADE"), nullable=False)
    recomFlashcardID = db.Column(db.Integer, db.ForeignKey('flashcard.id', ondelete="CASCADE"), nullable=False)
    ownerUserID = db.Column(db.Integer, db.ForeignKey('user.id', ondelete="CASCADE"), nullable=False)
    timeoutScore = db.Column(db.Float, default=1.0)

    target_user = db.relationship('User', foreign_keys=[targetUserID], backref=db.backref('timeout_cards_target', cascade="all, delete-orphan"))
    owner_user = db.relationship('User', foreign_keys=[ownerUserID], backref=db.backref('timeout_cards_owner', cascade="all, delete-orphan"))
    target_card = db.relationship('Flashcard', foreign_keys=[targetFlashcard], backref=db.backref('timeout_cards_target', cascade="all, delete-orphan"))
    recom_card = db.relationship('Flashcard', foreign_keys=[recomFlashcardID], backref=db.backref('timeout_cards_recom', cascade="all, delete-orphan"))

class TimeoutCollections(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    targetUserID = db.Column(db.Integer, db.ForeignKey('user.id', ondelete="CASCADE"), nullable=False)
    targetCollection = db.Column(db.Integer, db.ForeignKey('collection.id', ondelete="CASCADE"), nullable=False)
    recomCollectionID = db.Column(db.Integer, db.ForeignKey('collection.id', ondelete="CASCADE"), nullable=False)
    ownerUserID = db.Column(db.Integer, db.ForeignKey('user.id', ondelete="CASCADE"), nullable=False)
    timeoutScore = db.Column(db.Float, default=1.0)

    target_user = db.relationship('User', foreign_keys=[targetUserID], backref=db.backref('timeout_cols_target', cascade="all, delete-orphan"))
    owner_user = db.relationship('User', foreign_keys=[ownerUserID], backref=db.backref('timeout_cols_owner', cascade="all, delete-orphan"))
    target_col = db.relationship('Collection', foreign_keys=[targetCollection], backref=db.backref('timeout_cols_target', cascade="all, delete-orphan"))
    recom_col = db.relationship('Collection', foreign_keys=[recomCollectionID], backref=db.backref('timeout_cols_recom', cascade="all, delete-orphan"))