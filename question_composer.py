import json
import random

db = json.load(open('database.json'))

def equalize_chances(db):
    subset = []

    orders = ['Afrosoricida', 'Artiodactyla', 'Carnivora', 'Cetacea', 'Chiroptera', 'Cingulata', 'Dasyuromorphia',
              'Dermoptera', 'Didelphimorphia', 'Diprotodontia', 'Erinaceomorpha', 'Hyracoidea', 'Lagomorpha',
              'Macroscelidea', 'Microbiotheria', 'Monotremata', 'Notoryctemorphia', 'Paucituberculata', 'Peramelemorphia', 'Perissodactyla',
              'Pholidota', 'Pilosa', 'Primates', 'Proboscidea', 'Rodentia', 'Scandentia', 'Sirenia', 'Soricomorpha', 'Tubulidentata']

    orders_dict = {}
    for order in orders:
        orders_dict[order] = []

    for index in db['Species']:
        orders_dict[db['Order'][index]].append(index)

    for order in orders:
        order_species = orders_dict[order]
        species_to_select = min(100, len(order_species)) # 100 (or less if not possible) species from each order
        subset.extend(random.sample(order_species, species_to_select))

    return subset

equalized_subset = equalize_chances(db) #equalize once per session

def generate_one_other(column, value, similarity_column=None):
    indices = []
    if similarity_column is not None:
        for index in equalized_subset:
            if db[column].get(index) is not None and db[similarity_column].get(index) is not None:
                indices.append(index)
    else:
        for index in equalized_subset:
            if db[column].get(index) is not None:
                indices.append(index)
        
    def get_similarity_value(similarity_column):
        filter_values = []
        for index in indices:
                filter_values.extend(db[similarity_column].get(index).split('\n'))
        while True:
            filter_value = random.choice(filter_values)
            matched_count = 0
            unmatched_count = 0
            for index in indices:
                if filter_value in db[similarity_column][index]:
                    if value in db[column][index]:
                        matched_count+=1
                    else:
                        unmatched_count+=1
                if matched_count>=3 and unmatched_count>=1:
                    break
            if matched_count>=3 and unmatched_count>=1:
                return filter_value
                break
                
    selected = []
    if similarity_column is not None:
        similarity_value = get_similarity_value(similarity_column)
        while len(selected)<3:
            index = random.choice(indices)
            if index not in selected:
                if similarity_value in db[similarity_column][index]:
                    if value in db[column][index]:
                        selected.append(index)
        while len(selected)<4:
            index = random.choice(indices)
            if index not in selected:
                if similarity_value in db[similarity_column][index]:
                    if not value in db[column][index]:
                        selected.append(index)
    else:
        while len(selected)<3:
            index = random.choice(indices)
            if index not in selected:
                if value in db[column][index]:
                    selected.append(index)
        while len(selected)<4:
            index = random.choice(indices)
            if index not in selected:
                if not value in db[column][index]:
                    selected.append(index)
        
    #last one is correct
    
    results = []
    for index in selected:
        image_url = random.choice(db['images_cropped'].get(index))
        if language == 'rus':
            if db['name_rus'].get(index) is not None:
                name_eng = db['name_rus'].get(index)
            else:
                name_eng = db['name_eng'].get(index)
        else:
            name_eng = db['name_eng'].get(index)
        species = db['Species'].get(index)
        results.append([species, name_eng, image_url])
        
    return results

def generate_question(column, lang):
    global language
    language = lang
    if column == 'Biogeographic Regions':
        values = ['Nearctic', 'Palearctic', 'Oriental', 'Ethiopian', 'Neotropical', 'Australian']
        descriptions = ['North America', 'Europe, North Asia and North Africa', 'India and Southeast Asia', 'Sub-Saharan Africa and South Arabia', 'Central and South America', 'Australia, New Zealand and New Guinea']
        value = random.choice(values)
        description = descriptions[values.index(value)]
        similarity_column = 'Habitat Regions'

        values_rus = [u'Неарктическом', u'Палеарктическом', u'Индомалайском', u'Афротропическом', u'Неотропическом', u'Австралийском']
        value_rus = values_rus[values.index(value)]
        descriptions_rus = [u'Северная Америка', u'Европа, Северная Азия и Северная Африка', u'Индия и Юго-Восточная Азия', u'Африка к югу от Сахары и Южная Аравия', u'Центральная и Южная Америка', u'Австралия, Новая Зеландия и Новая Гвинея']
        description_rus = descriptions_rus[values.index(value)]
        
        results = generate_one_other(column, value, similarity_column)
        if language == 'rus':
            question = u'Какое из этих животных не живет в '+value_rus+u' царстве ('+description_rus+u')?'
        else:
            question = "Which of these animals doesn't live in "+value+" realm ("+description+")?"
        
        numbers = range(4)
        random.shuffle(numbers)
        
        results_shuffled = [results[i] for i in numbers]
        answer = numbers.index(3)+1 #last one was correct
        
        annotation = [res[1]+' ('+res[0]+')' for res in results_shuffled]
        images = [res[2] for res in results_shuffled]
        
        return {'question': question, 'answer': answer, 'annotation': annotation, 'images': images}
    elif column == 'Species':
        species_indices = []
        for index in equalized_subset:
            if len(db['images_cropped'].get(index))>=3:
                species_indices.append(index)
        while True:
            selected_index = random.choice(species_indices)
            family = db['Family'][selected_index]
            similar_species = []
            for index in db[column]:
                if db['Family'][index] == family and index != selected_index:
                    similar_species.append(index)
            if len(similar_species)>=1:
                def get_name(index):
                    if language == 'rus' and db['name_rus'].get(index) is not None:
                        return db['name_rus'].get(index)
                    else:
                        return db['name_eng'].get(index)
                
                selected_similar_index = random.choice(similar_species)
                images = random.sample(db['images_cropped'][selected_index], 3) + [random.choice(db['images_cropped'][selected_similar_index])]
                annotation = [get_name(index)+' ('+db['Species'][index]+')' for index in [selected_index]*3 + [selected_similar_index]]

                if language == 'rus':
                    first_part = u'Кто из них не '
                else:
                    first_part = 'Which one is not '
                question = first_part+get_name(selected_index)+' ('+db['Species'][selected_index]+')?'

                numbers = range(4)
                random.shuffle(numbers)
                answer = numbers.index(3)+1
                images_shuffled = [images[i] for i in numbers]
                annotation_shuffled = [annotation[i] for i in numbers]

                return {'question': question, 'answer': answer, 'annotation': annotation_shuffled, 'images': images_shuffled}
                break
    elif column in ('Primary Diet basic', 'Primary Diet detailed'):
        if column == 'Primary Diet basic':
            mode = 'basic'
        else:
            mode = 'detailed'
        column = 'Primary Diet'

        if language == 'rus':
            values_dict_basic = {'Carnivore': u'питается другими животными', 'Herbivore': u'питается растениями', 'Omnivore': u'питается растениями и животными',
                                 'Planktivore': u'питается планктоном', 'Mycophage': u'питается грибами', 'Detritivore': u'питается разложившимися животными или растениями',
                                 'Coprophage': u'питается фекалиями'}
            values_dict_carnivore = {'Eats terrestrial vertebrates': u'ест мясо', 'Piscivore': u'ест рыбу', 'Eats eggs': u'ест яйца',
                                     'Sanguivore': u'пьет кровь', 'Insectivore': u'ест насекомых или пауков',
                                     'Molluscivore': u'ест моллюсков', 'Vermivore': u'ест червей', 'Scavenger': u'питается падалью'}
            values_dict_herbivore = {'Folivore': u'ест листья и цветы', 'Frugivore': u'ест фрукты', 'Granivore': u'ест зерна, семена и орехи',
                                     'Lignivore': u'ест древесину, кору и почки', 'Nectarivore': u'пьет нектар', 'Algivore': u'ест водоросли'}
        else:
            values_dict_basic = {'Carnivore': 'mainly eats animals', 'Herbivore': 'mainly eats plants', 'Omnivore': 'eats plants and animals',
                                 'Planktivore': 'eats plankton', 'Mycophage': 'eats mushrooms', 'Detritivore': 'eats decomposed plant or animals',
                                 'Coprophage': 'eats fecal matter'}
            values_dict_carnivore = {'Eats terrestrial vertebrates': 'eats meat', 'Piscivore': 'eats fish', 'Eats eggs': 'eats eggs',
                                     'Sanguivore': 'drinks blood', 'Insectivore': 'eats insects and spiders',
                                     'Molluscivore': 'eats molluscs', 'Vermivore': 'eats worms', 'Scavenger': 'eats decaying dead animals'}
            values_dict_herbivore = {'Folivore': 'eats leaves and flowers', 'Frugivore': 'eats fruits', 'Granivore': 'eats grains, seeds and nuts',
                                     'Lignivore': 'eats wood, bark or stems', 'Nectarivore': 'drinks nectar', 'Algivore': 'eats seaweeds'}

        if mode == 'basic':
            value = random.choice(['Carnivore', 'Herbivore', 'Omnivore'])
            values_rus = {'Carnivore': u'плотоядное', 'Herbivore': u'травоядное', 'Omnivore': u'всеядное'}
            value_rus = values_rus[value]
            description = values_dict_basic[value]
            similarity_value = None
            if language == 'rus':
                question = u'Какое из этих животных '+value_rus+u' ('+description+u')?'
            else:
                question = 'Which of these animals is '+value+' ('+description+')?'
                             
        elif mode == 'detailed':
            while True: #test values
                c = 0
                value = random.choice(['Planktivore', 'Mycophage', 'Detritivore', 'Coprophage'] + values_dict_carnivore.keys() + values_dict_herbivore.keys())
                for index in equalized_subset:
                    if db[column].get(index) is not None:
                        if value in db[column].get(index):
                            c+=1
                            break
                if c==1:
                    break
                    
            if value in values_dict_basic:
                description = values_dict_basic[value]
                similarity_value = None
            elif value in values_dict_carnivore:
                description = values_dict_carnivore[value]
                similarity_value = 'Carnivore'
            elif value in values_dict_herbivore:
                description = values_dict_herbivore[value]
                similarity_value = 'Herbivore'

            if language == 'rus':
                question = u'Какое из этих животных '+description+u'?'
            else:
                question = 'Which of these animals '+description+'?'
            
        have_value = []
        dont_have_value = []
        
        for index in equalized_subset:
            if db[column].get(index) is not None:
                if similarity_value is None or similarity_value in db[column][index]:
                    if value in db[column][index]:
                        have_value.append(index)
                    else:
                        dont_have_value.append(index)
                            
        correct = random.choice(have_value)
        incorrect = random.sample(dont_have_value, 3)
        
        selected = incorrect + [correct]
        
        images = [random.choice(db['images_cropped'].get(index)) for index in selected]
        def get_name(index):
            if language == 'rus' and db['name_rus'].get(index) is not None:
                return db['name_rus'].get(index)
            else:
                return db['name_eng'].get(index)
        
        if mode=='detailed':
            annotation = [get_name(index)+' ('+db['Species'].get(index)+')' for index in selected]
        elif mode=='basic':
            if language == 'rus':
                annotation = [get_name(index)+u'\n(Всеядное)' if 'Omnivore' in db[column][index]
                              else get_name(index)+u'\n(Травоядное)' if 'Herbivore' in db[column][index]
                              else get_name(index)+u'\n(Плотоядное)' if 'Carnivore' in db[column][index]
                              else get_name(index)+u'\n(Другое)'
                              for index in selected]
            else:
                annotation = [db['name_eng'][index]+'\n(Omnivore)' if 'Omnivore' in db[column][index]
                              else db['name_eng'][index]+'\n(Herbivore)' if 'Herbivore' in db[column][index]
                              else db['name_eng'][index]+'\n(Carnivore)' if 'Carnivore' in db[column][index]
                              else db['name_eng'][index]+'\n(Other)'
                              for index in selected]
            
        numbers = range(4)
        random.shuffle(numbers)
        answer = numbers.index(3)+1
        images_shuffled = [images[i] for i in numbers]
        annotation_shuffled = [annotation[i] for i in numbers]

        return {'question': question, 'answer': answer, 'annotation': annotation_shuffled, 'images': images_shuffled}

    elif column == 'Lifespan (wild, undetermined) - undetermined - average - years' or column == 'Lifespan (captivity, undetermined) - undetermined - average - years':
        indices = []
        for index in equalized_subset:
            if db[column].get(index) is not None and db[column].get(index) != 0:
                indices.append(index)

        while True:
            selected_indices = random.sample(indices, 4)
            lifespans = []
            for index in selected_indices:
                lifespans.append(db[column][index])
                
            # ensure that no animals in sample have equal rounded lifespan
            passflag = True
            for i, ls in enumerate(lifespans):
                row = [abs(x-ls) for x in lifespans]
                for j, el in enumerate(row):
                    if i==j or el>=1:
                        pass
                    else:
                        passflag = False
                        break
                if not passflag:
                    break
                    
            if max(lifespans)-min(lifespans)<5: # range at least 5 years
                passflag = False

            if passflag:
                break

        min_max = random.choice(['min', 'max'])
        
        if min_max == 'max':
            if 'wild' in column:
                if language == 'rus':
                    question = u'Какое из этих животных живет дольше других (в природе, в среднем)?'
                else:
                    question = 'Which of these animals lives longer than others (in wild, on average)?'
            elif 'captivity' in column:
                if language == 'rus':
                    question = u'Какое из этих животных живет дольше других (в неволе, в среднем)?'
                else:
                    question = 'Which of these animals lives longer than others (in captivity, on average)?'

            answer = lifespans.index(max(lifespans))+1
        
        elif min_max == 'min':
            if 'wild' in column:
                if language == 'rus':
                    question = u'Какое из этих животных живет меньше других (в природе, в среднем)?'
                else:
                    question = 'Which of these animals lives less than others (in wild, on average)?'
            elif 'captivity' in column:
                if language == 'rus':
                    question = u'Какое из этих животных живет меньше других (в неволе, в среднем)?'
                else:
                    question = 'Which of these animals lives less than others (in captivity, on average)?'

            answer = lifespans.index(min(lifespans))+1

        def get_name(index):
                if language == 'rus' and db['name_rus'].get(index) is not None:
                    return db['name_rus'].get(index)
                else:
                    return db['name_eng'].get(index)
            
        images = [random.choice(db['images_cropped'][index]) for index in selected_indices]
        if language == 'rus':
            annotation = [get_name(index)+'\n('+str(round(db[column][index],1))+u' лет)' if int(round(db[column][index])) == 0
                          else get_name(index)+u'\n(1 год)' if int(round(db[column][index])) == 1
                          else get_name(index)+'\n('+str(int(round(db[column][index])))+u' лет)'
                          for index in selected_indices]
        else:
            annotation = [db['name_eng'][index]+'\n('+str(round(db[column][index],1))+' years)' if int(round(db[column][index])) == 0
                  else db['name_eng'][index]+'\n(1 year)' if int(round(db[column][index])) == 1
                  else db['name_eng'][index]+'\n('+str(int(round(db[column][index])))+' years)'
                  for index in selected_indices]

        return {'question': question, 'answer': answer, 'annotation': annotation, 'images': images}

    elif column == 'IUCN Red List':
        values = ['Critically Endangered', 'Endangered', 'Extinct in the Wild',
                  'Least Concern', 'Near Threatened', 'Vulnerable']
        skip_values = ['Not Evaluated', 'Data Deficient', 'No special status', 'Extinct']

        while True: #test values
            c = 0
            value = random.choice(values)
            for index in equalized_subset:
                if db[column].get(index) is not None:
                    if db[column][index] == 'None: '+value:
                        c+=1
                        break
            if c==1:
                break

        values_rus = [u'В критической опасности', u'Под угрозой', u'Вымерший', u'Исчезнувший в природе',
                  u'Вызывающий наименьшие опасения', u'Близкий к уязвимому положению', u'Уязвимый']

        if language == 'rus':
            value_rus = values_rus[values.index(value)]
            question = u'Какое из этих животных имеет охранный статус "'+value_rus+u'"?'
        else:
            question = "Which of these animals has '"+value+"' conservation status according to the IUCN Red List?"
        
        indices = []
        for index in equalized_subset:
            if db[column].get(index) is not None:
                if db[column][index] not in ['None: '+sval for sval in skip_values]:
                    indices.append(index)

        have_value = []
        dont_have_value = []
        
        for index in indices:
            if db[column][index] == 'None: '+value:
                have_value.append(index)
            else:
                dont_have_value.append(index)

        correct = random.choice(have_value)
        incorrect = random.sample(dont_have_value, 3)
        
        selected = incorrect + [correct]
        
        images = [random.choice(db['images_cropped'][index]) for index in selected]

        def get_name(index):
            if language == 'rus' and db['name_rus'].get(index) is not None:
                return db['name_rus'].get(index)
            else:
                return db['name_eng'].get(index)

        if language == 'rus':
            annotation = [get_name(index)+'\n('+values_rus[values.index(db[column][index][6:])]+')' for index in selected]
        else:
            annotation = [db['name_eng'][index]+'\n('+db[column][index][6:]+')' for index in selected]
        
        numbers = range(4)
        random.shuffle(numbers)
        answer = numbers.index(3)+1
        images_shuffled = [images[i] for i in numbers]
        annotation_shuffled = [annotation[i] for i in numbers]

        return {'question': question, 'answer': answer, 'annotation': annotation_shuffled, 'images': images_shuffled}

    elif column=='Family':
        indices = []
        for index in equalized_subset:
            if db[column].get(index) is not None:
                indices.append(index)

        while True:
            selected_index = random.choice(indices)
            selected_family = db[column][selected_index]
            selected_order = db['Order'][selected_index]

            same_family=[]
            for index in indices:
                if db[column][index]==selected_family and index!=selected_index:
                    same_family.append(index)

            same_order=[]
            for index in indices:
                if db['Order'][index]==selected_order and index!=selected_index and index not in same_family:
                    same_order.append(index)

            if len(same_order)>=2 and len(same_family)>=1:
                selected = random.sample(same_order, 2) + [random.choice(same_family)] + [selected_index]
                break

        def get_name(index):
            if language == 'rus' and db['name_rus'].get(index) is not None:
                return db['name_rus'].get(index)
            else:
                return db['name_eng'].get(index)

        images = [random.choice(db['images_cropped'][index]) for index in selected]
        if language == 'rus':
            annotation = [get_name(index)+' ('+db['Species'][index]+')' for index in selected]
        else:
            annotation = [db['name_eng'][index]+' ('+db['Species'][index]+')' for index in selected]
        
        numbers_first = range(3)
        random.shuffle(numbers_first)
        answer = numbers_first.index(2)+1
        numbers = numbers_first + [3]
        preselect = 4
        images_shuffled = [images[i] for i in numbers]
        annotation_shuffled = [annotation[i] for i in numbers]

        if language == 'rus':
            question = u"Найдите здесь ближайшего родственника животного "+get_name(selected_index)
        else:
            question = "Find "+db['name_eng'][selected_index]+"'s closest relative"

        return {'question': question, 'answer': answer, 'annotation': annotation_shuffled,
                'images': images_shuffled, 'preselect': preselect}

    elif column=='Mass - average - g':
        indices = []
        for index in equalized_subset:
            if db[column].get(index) is not None:
                indices.append(index)

        while True:
            selected_indices = random.sample(indices, 4)
            masses = []
            for index in selected_indices:
                masses.append(db[column][index]*1./1000)
                
            # ensure that no animals in sample have equal rounded mass in kg
            passflag = True
            for i, m in enumerate(masses):
                row = [abs(x-m) for x in masses]
                for j, el in enumerate(row):
                    if i==j or el>=1:
                        pass
                    else:
                        passflag = False
                        break
                if not passflag:
                    break
                    
            if max(masses)-min(masses)<5 and min(masses)>0: # range at least 5 kg and no animal has zero weight
                passflag = False

            if passflag:
                break

        min_max = random.choice(['min', 'max'])
        
        if min_max == 'max':
            if language == 'rus':
                question = u'Какое из этих животных весит больше других?'
            else:
                question = 'Which animal is the heaviest?'
            answer = masses.index(max(masses))+1
        
        elif min_max == 'min':
            if language == 'rus':
                question = u'Какое животное весит меньше других?'
            else:
                question = 'Which animal weighs less than others?'
            answer = masses.index(min(masses))+1

        def get_name(index):
            if language == 'rus' and db['name_rus'].get(index) is not None:
                return db['name_rus'].get(index)
            else:
                return db['name_eng'].get(index)
            
        images = [random.choice(db['images_cropped'][index]) for index in selected_indices]
        if language == 'rus':
            annotation = [get_name(index)+'\n('+str(int(round(db[column][index])))+u' г)' if db[column][index]<1000
                          else get_name(index)+'\n('+str(int(round(db[column][index]*1./1000)))+u' кг)'
                          for index in selected_indices]
        else:
            annotation = [db['name_eng'][index]+'\n('+str(int(round(db[column][index])))+' g)' if db[column][index]<1000
                          else db['name_eng'][index]+'\n('+str(int(round(db[column][index]*1./1000)))+' kg)'
                          for index in selected_indices]

        return {'question': question, 'answer': answer, 'annotation': annotation, 'images': images}

    elif column=='Mating System':
        indices = []
        for index in equalized_subset:
            if db[column].get(index) is not None:
                indices.append(index)

        if language == 'rus':
            question = u'Какое из этих животных моногамное (имеет постоянную пару)?'
        else:
            question = 'Which of these animals is monogamous (one male and one female mate)?'
        value = 'Monogamous'

        have_value = []
        dont_have_value = []
        
        for index in indices:
            if value in db[column][index]:
                have_value.append(index)
            else:
                dont_have_value.append(index)

        correct = random.choice(have_value)
        incorrect = random.sample(dont_have_value, 3)
        
        selected = incorrect + [correct]
        
        images = [random.choice(db['images_cropped'][index]) for index in selected]

        def get_name(index):
            if language == 'rus' and db['name_rus'].get(index) is not None:
                return db['name_rus'].get(index)
            else:
                return db['name_eng'].get(index)
        annotation = [get_name(index)+'\n('+db['Species'][index]+')' for index in selected]
        
        numbers = range(4)
        random.shuffle(numbers)
        answer = numbers.index(3)+1
        images_shuffled = [images[i] for i in numbers]
        annotation_shuffled = [annotation[i] for i in numbers]

        return {'question': question, 'answer': answer, 'annotation': annotation_shuffled, 'images': images_shuffled}

    elif column=='Sexual Dimorphism':
        indices = []
        for index in equalized_subset:
            if db[column].get(index) is not None:
                indices.append(index)
                
        values_dict = {'Male larger': 'males larger than females', 'Female larger': 'females larger than males'}
        values_dict_rus = {'Male larger': u'самцы крупнее самок', 'Female larger': u'самки крупнее самцов'}
        value = random.choice(values_dict.keys())
        if language == 'rus':
            description = values_dict_rus[value]
            question = u'У какого из этих видов животных '+description+'?'
        else:
            description = values_dict[value]
            question = 'Which of these species has '+description+'?'

        def get_name(index):
            if language == 'rus' and db['name_rus'].get(index) is not None:
                return db['name_rus'].get(index)
            else:
                return db['name_eng'].get(index)

        have_value = []
        dont_have_value = []
        
        for index in indices:
            if value in db[column][index]:
                have_value.append(index)
            else:
                dont_have_value.append(index)

        correct = random.choice(have_value)
        incorrect = random.sample(dont_have_value, 3)
        
        selected = incorrect + [correct]
        
        images = [random.choice(db['images_cropped'][index]) for index in selected]
        if language == 'rus':
            annotation = [get_name(index)+u'\n(самцы крупнее)' if 'Male larger' in db[column][index]
                          else get_name(index)+u'\n(самки крупнее)' if 'Female larger' in db[column][index]
                          else get_name(index)+u'\n(одинаково крупные)' for index in selected]
        else:
            annotation = [db['name_eng'][index]+'\n(Male larger)' if 'Male larger' in db[column][index]
                          else db['name_eng'][index]+'\n(Female larger)' if 'Female larger' in db[column][index]
                          else db['name_eng'][index]+'\n(Sexes alike)' for index in selected]
        
        numbers = range(4)
        random.shuffle(numbers)
        answer = numbers.index(3)+1
        images_shuffled = [images[i] for i in numbers]
        annotation_shuffled = [annotation[i] for i in numbers]

        return {'question': question, 'answer': answer, 'annotation': annotation_shuffled, 'images': images_shuffled}

    elif column=='Terrestrial Biomes':
        indices = []
        for index in equalized_subset:
            if db[column].get(index) is not None:
                indices.append(index)

        values = ['Tundra', 'Taiga', 'Desert or dune', 'Savanna or grassland', 'Chaparral', 'Forest', 'Rainforest', 'Scrub forest',
                  'Mountains', 'Icecap']
        q_values_rus = [u'тундре', u'тайге', u'пустыне', u'саванне или на лугах', u'зарослях вечнозеленых кустарников', u'лесах', u'дождевых лесах', u'кустарниковой степи', u'горах', u'покрытых льдом местностях']
        values_rus = [u'Тундра', u'Тайга', u'Пустыня', u'Саванна', u'Заросли вечнозеленых кустарников', u'Леса', u'Дождевые леса', u'Кустарниковая степь', u'Горы', u'Покрытые льдом местности']
        sources = ['https://c1.staticflickr.com/5/4272/34118511394_af21a66f7d_o.jpg', 'https://c1.staticflickr.com/5/4220/34921130366_8041486184_o.jpg', 'https://c1.staticflickr.com/5/4227/34921129916_4063cbe6a6_o.jpg', 'https://c1.staticflickr.com/5/4246/34118511704_d8bcd43d18_o.jpg', 'https://c1.staticflickr.com/5/4276/34961653945_d170332a5e_o.jpg', 'https://c1.staticflickr.com/5/4204/34921130506_d0b8e20d7d_o.jpg', 'https://c1.staticflickr.com/5/4243/34961654025_2e75925f2e_o.jpg', 'https://c1.staticflickr.com/5/4202/34118512104_c916f35384_o.jpg', 'https://c1.staticflickr.com/5/4201/34921130236_dcc4bc8350_o.jpg', 'https://c1.staticflickr.com/5/4200/34961654175_79290f6a9a_o.jpg']

        value = random.choice(values)
        q_value_rus = q_values_rus[values.index(value)]
        value_rus = values_rus[values.index(value)]
        source = sources[values.index(value)]

        if language == 'rus':
            question = u'Какое из этих животных живет в '+q_value_rus+u'?'
        else:
            question = 'Which of these animals lives in '+value+'?'

        have_value = []
        dont_have_value = []
        
        for index in indices:
            if value in db[column][index]:
                have_value.append(index)
            else:
                dont_have_value.append(index)

        correct = random.choice(have_value)
        incorrect = random.sample(dont_have_value, 2)
        
        selected = incorrect + [correct]

        def get_name(index):
            if language == 'rus' and db['name_rus'].get(index) is not None:
                return db['name_rus'].get(index)
            else:
                return db['name_eng'].get(index)

        images = [random.choice(db['images_cropped'][index]) for index in selected]

        if language == 'rus':
            annotation = [get_name(index)+'\n('+', '.join([values_rus[values.index(val)] for val in db[column][index].split('\n')])+')' for index in selected]
        else:
            annotation = [db['name_eng'][index]+'\n('+', '.join(db[column][index].split('\n'))+')' for index in selected]
        
        numbers = range(3)
        random.shuffle(numbers)
        answer = numbers.index(2)+1
        images_shuffled = [images[i] for i in numbers] + [source]
        if language == 'rus':
            annotation_shuffled = [annotation[i] for i in numbers] + [value_rus]
        else:
            annotation_shuffled = [annotation[i] for i in numbers] + [value]

        return {'question': question, 'answer': answer, 'annotation': annotation_shuffled, 'images': images_shuffled, 'preselect': 4}

    elif column=='Puzzle':
        indices = []
        for index in equalized_subset:
            if db['parts'].get(index) is not None:
                indices.append(index)

        def get_name(index):
            if language == 'rus' and db['name_rus'].get(index) is not None:
                return db['name_rus'].get(index)
            else:
                return db['name_eng'].get(index)
        
        parts = []
        while len(parts) not in [9,16,25]: #check if puzzle is not broken
            selected_index = random.choice(indices)
            species = db['Species'][selected_index]
            name = get_name(selected_index)
            parts = random.choice(db['parts'].get(selected_index))

        if language == 'rus':
            question = u'Соберите из фрагментов фотографию животного\n'+name+u' ('+species+u')'
        else:
            question = "Swap parts to get "+name+"'s ("+species+") picture"
        
        return {'question': question, 'parts': parts}

    elif column=='Key Behaviors':
        indices = []
        for index in equalized_subset:
            if db[column].get(index) is not None:
                indices.append(index)

        values = ['hibernation', 'migratory', 'nomadic', 'flies', 'glides', 'nocturnal', 'arboreal', 'cursorial', 'fossorial', 
                  'troglophilic', 'saltatorial', 'solitary', 'colonial', 'territorial']
        descriptions = ['hibernates (is inactive during the winter)', 'migrates (moves seasonally between different regions)',
                        'is nomadic (moves throughout a large range year-round)', 'flies', 'glides', 'is nocturnal (active at night)',
                        'lives in trees', 'runs well', 'lives under ground', 'lives in caves', 'jumps or hops well', 'lives alone', 'lives in large groups', 'defends its area']
        descriptions_rus = [u'впадает в зимнюю спячку', u'мигрирует в зависимости от времени года', u'ведет кочевой образ жизни', u'умеет летать', u'умеет планировать', u'ведет ночной образ жизни',
                        u'живет на деревьях', u'хорошо бегает', u'живет под землей', u'живет в пещерах', u'хорошо прыгает', u'ведет одиночный образ жизни',
                        u'живет в больших группах', u'занимает и определенную территорию и защищает ее']

        value = random.choice(values)
        description = descriptions[values.index(value)]
        description_rus = descriptions_rus[values.index(value)]

        if language == 'rus':
            question = u'Какое из этих животных '+description_rus+u'?'
        else:
            question = 'Which of these animals '+description+'?'

        have_value = []
        dont_have_value = []
        
        for index in indices:
            if value in db[column][index]:
                have_value.append(index)
            else:
                dont_have_value.append(index)

        correct = random.choice(have_value)
        incorrect = random.sample(dont_have_value, 3)
        
        selected = incorrect + [correct]

        def get_name(index):
            if language == 'rus' and db['name_rus'].get(index) is not None:
                return db['name_rus'].get(index)
            else:
                return db['name_eng'].get(index)

        images = [random.choice(db['images_cropped'][index]) for index in selected]
        annotation = [get_name(index)+'\n('+db['Species'][index]+')' for index in selected]
        
        numbers = range(4)
        random.shuffle(numbers)
        answer = numbers.index(3)+1
        images_shuffled = [images[i] for i in numbers]
        annotation_shuffled = [annotation[i] for i in numbers]

        return {'question': question, 'answer': answer, 'annotation': annotation_shuffled, 'images': images_shuffled}
    
    elif column=='Positive Impacts':
        indices = []
        for index in equalized_subset:
            if db[column].get(index) is not None:
                indices.append(index)

        values = ['pet trade', 'food', 'body parts are source of valuable material', 'source of medicine or drug', 'research and education', 'controls pest population']
        descriptions = ['are kept as pets', 'give people food', 'give people valuable materials', 'are used in health care', 'are used in research and education', 'control pest population']
        descriptions_rus = [u'содержится в качестве домашнего животного', u'употребляется людьми в пищу', u'дает людям ценные материалы', u'используется в медицине', u'используется в исследованиях и образовании', u'контролирует популяцию вредителей']

        have_value = []
        dont_have_value = []
        
        while len(have_value) == 0:
            value = random.choice(values)
            description = descriptions[values.index(value)]
            description_rus = descriptions_rus[values.index(value)]

            if language == 'rus':
                question = u'Укажите животное, которое '+description_rus
            else:
                question = 'Which of these animals '+description+'?'
        
            for index in indices:
                if value in db[column][index]:
                    have_value.append(index)
                else:
                    dont_have_value.append(index)

        correct = random.choice(have_value)
        incorrect = random.sample(dont_have_value, 3)
        
        selected = incorrect + [correct]

        images = [random.choice(db['images_cropped'][index]) for index in selected]
        
        def get_name(index):
            if language == 'rus' and db['name_rus'].get(index) is not None:
                return db['name_rus'].get(index)
            else:
                return db['name_eng'].get(index)
        annotation = [get_name(index)+'\n('+db['Species'][index]+')' for index in selected]
        
        numbers = range(4)
        random.shuffle(numbers)
        answer = numbers.index(3)+1
        images_shuffled = [images[i] for i in numbers]
        annotation_shuffled = [annotation[i] for i in numbers]

        return {'question': question, 'answer': answer, 'annotation': annotation_shuffled, 'images': images_shuffled}
    
    elif column=='Negative Impacts':
        indices = []
        for index in equalized_subset:
            if db[column].get(index) is not None:
                indices.append(index)

        values = ['causes disease in humans', 'causes or carries domestic animal disease', 'crop pest', 'household pest', 'carries human disease', 'venomous']
        descriptions = ['causes human disease', 'causes or carries domestic animal disease', 'is crop pest', 'is household pest', 'carries human disease', 'is venomous (can inject poison)', 'is poisonous (has dangerous substances)']
        descriptions_rus = [u'вызывает болезни человека', u'вызывает или переносит болезни домашних животных', u'является сельскохозяйственным вредителем', u'является вредителем домашнего хозяйства', u'переносит человеческие болезни', u'ядовитое (может впрыскивать яд)', u'ядовитое (имеет ядовитые части тела)']

        have_value = []
        dont_have_value = []
        
        while len(have_value) == 0:
            value = random.choice(values)
            description = descriptions[values.index(value)]
            description_rus = descriptions_rus[values.index(value)]

            if language == 'rus':
                question = u'Какое из этих животных '+description_rus+'?'
            else:
                question = 'Which of these animals '+description+'?'
        
            for index in indices:
                if value in db[column][index]:
                    have_value.append(index)
                else:
                    dont_have_value.append(index)

        correct = random.choice(have_value)
        incorrect = random.sample(dont_have_value, 3)
        
        selected = incorrect + [correct]

        images = [random.choice(db['images_cropped'][index]) for index in selected]

        def get_name(index):
            if language == 'rus' and db['name_rus'].get(index) is not None:
                return db['name_rus'].get(index)
            else:
                return db['name_eng'].get(index)
        annotation = [get_name(index)+'\n('+db['Species'][index]+')' for index in selected]
        
        numbers = range(4)
        random.shuffle(numbers)
        answer = numbers.index(3)+1
        images_shuffled = [images[i] for i in numbers]
        annotation_shuffled = [annotation[i] for i in numbers]

        return {'question': question, 'answer': answer, 'annotation': annotation_shuffled, 'images': images_shuffled}

    elif column=='Key Reproductive Features':
        indices = []
        for index in equalized_subset:
            if db[column].get(index) is not None:
                indices.append(index)

        values = ['Seasonal breeding', 'Year-round breeding']
        values_rus = [u'имеет определенные сезоны размножения', u'может размножаться в течение всего года']

        have_value = []
        dont_have_value = []
        
        while len(have_value) == 0:
            value = random.choice(values)
            q_value_rus = values_rus[values.index(value)]
            value_rus = values_rus[values.index(value)]

            if language == 'rus':
                question = u'Какое из этих животных '+q_value_rus+u'?'
            else:
                question = 'Which of these animals has '+value.lower()+'?'
        
            for index in indices:
                if value in db[column][index]:
                    have_value.append(index)
                else:
                    dont_have_value.append(index)

        correct = random.choice(have_value)
        incorrect = random.sample(dont_have_value, 3)
        
        selected = incorrect + [correct]

        images = [random.choice(db['images_cropped'][index]) for index in selected]

        def get_name(index):
            if language == 'rus' and db['name_rus'].get(index) is not None:
                return db['name_rus'].get(index)
            else:
                return db['name_eng'].get(index)
        annotation = [get_name(index)+'\n('+db['Species'][index]+')' for index in selected]
        
        numbers = range(4)
        random.shuffle(numbers)
        answer = numbers.index(3)+1
        images_shuffled = [images[i] for i in numbers]
        annotation_shuffled = [annotation[i] for i in numbers]

        return {'question': question, 'answer': answer, 'annotation': annotation_shuffled, 'images': images_shuffled}
    
    elif column=='Communication Channels':
        indices = []
        for index in equalized_subset:
            if db[column].get(index) is not None:
                indices.append(index)

        values = ['visual', 'tactile', 'acoustic', 'chemical', 'electric']
        values_rus = [u'визуальные', u'тактильные', u'акустические', u'химические', u'электрические']

        have_value = []
        dont_have_value = []
        
        while len(have_value) == 0:
            value = random.choice(values)
            value_rus = values_rus[values.index(value)]

            if language == 'rus':
                question = u'Какое из этих животных использует '+value_rus+u' каналы коммуникации?'
            else:
                question = 'Which of these animals uses '+value+' communication channels?'
        
            for index in indices:
                if value in db[column][index]:
                    have_value.append(index)
                else:
                    dont_have_value.append(index)

        correct = random.choice(have_value)
        incorrect = random.sample(dont_have_value, 3)
        
        selected = incorrect + [correct]

        images = [random.choice(db['images_cropped'][index]) for index in selected]

        def get_name(index):
            if language == 'rus' and db['name_rus'].get(index) is not None:
                return db['name_rus'].get(index)
            else:
                return db['name_eng'].get(index)

        if language != 'rus':
            annotation = [db['name_eng'][index]+'\n('+', '.join([s.capitalize() for s in db[column][index].split('\n')])+')' for index in selected]
        else:
            annotation = [get_name(index)+'\n('+', '.join([values_rus[values.index(s)] for s in db[column][index].split('\n')])+')' for index in selected]
        
        numbers = range(4)
        random.shuffle(numbers)
        answer = numbers.index(3)+1
        images_shuffled = [images[i] for i in numbers]
        annotation_shuffled = [annotation[i] for i in numbers]

        return {'question': question, 'answer': answer, 'annotation': annotation_shuffled, 'images': images_shuffled}
    
    elif column=='Perception Channels':
        indices = []
        for index in equalized_subset:
            if db[column].get(index) is not None:
                indices.append(index)

        values = ['infrared/heat', 'ultrasound', 'echolocation', 'magnetic']
        descriptions = ["has infrared vision (can detect heat)", "can hear ultrasound (sounds above human hearing range)", "uses echolocation", "has ability to detect Earth's magnetic fields"]
        descriptions_rus = [u"обладает инфракрасным зрением (может выявлять теплые участки)", u"может слышать ультразвук (звуки выше диапазона слышимости человека)", u"использует эхолокацию", u"обладает способностью чувствовать магнитные поля Земли"]

        have_value = []
        dont_have_value = []
        
        while len(have_value) == 0:
            value = random.choice(values)
            description = descriptions[values.index(value)]
            description_rus = descriptions_rus[values.index(value)]

            if language == 'rus':
                question = u'Какое из этих животных '+description_rus+u'?'
            else:
                question = 'Which of these animals '+description+'?'
        
            for index in indices:
                if value in db[column][index]:
                    have_value.append(index)
                else:
                    dont_have_value.append(index)

        correct = random.choice(have_value)
        incorrect = random.sample(dont_have_value, 3)
        
        selected = incorrect + [correct]

        images = [random.choice(db['images_cropped'][index]) for index in selected]
        
        def get_name(index):
            if language == 'rus' and db['name_rus'].get(index) is not None:
                return db['name_rus'].get(index)
            else:
                return db['name_eng'].get(index)
        annotation = [get_name(index)+'\n('+db['Species'][index]+')' for index in selected]
        
        numbers = range(4)
        random.shuffle(numbers)
        answer = numbers.index(3)+1
        images_shuffled = [images[i] for i in numbers]
        annotation_shuffled = [annotation[i] for i in numbers]

        return {'question': question, 'answer': answer, 'annotation': annotation_shuffled, 'images': images_shuffled}
    
    elif column=='Parental Investment':
        indices = []
        for index in equalized_subset:
            if db[column].get(index) is not None:
                indices.append(index)

        values = ['Male parental care', 'Female parental care']

        female = []
        both = []

        for index in indices:
            if values[0] in db[column][index] and values[1] in db[column][index]:
                both.append(index)
            elif values[1] in db[column][index]:
                female.append(index)
                
        options = ['female', 'both']
        option = random.choice(options)
        
        if option == 'female':
            if language == 'rus':
                question = u'Укажите вид животных, у которого о потомстве заботятся преимущественно самки'
            else:
                question = 'Choose an animal whose children are mostly cared by female individuals'
            correct = random.choice(female)
            incorrect = random.sample(both, 3)
        elif option == 'both':
            if language == 'rus':
                question = u'Укажите вид животных, у которого о потомстве одинаково заботятся и самки, и самцы'
            else:
                question = 'Choose an animal whose children are equally cared by individuals of both sexes'
            correct = random.choice(both)
            incorrect = random.sample(female, 3)
        
        selected = incorrect + [correct]

        images = [random.choice(db['images_cropped'][index]) for index in selected]
        def get_name(index):
            if language == 'rus' and db['name_rus'].get(index) is not None:
                return db['name_rus'].get(index)
            else:
                return db['name_eng'].get(index)
        annotation = [get_name(index)+'\n('+db['Species'][index]+')' for index in selected]
        
        numbers = range(4)
        random.shuffle(numbers)
        answer = numbers.index(3)+1
        images_shuffled = [images[i] for i in numbers]
        annotation_shuffled = [annotation[i] for i in numbers]

        return {'question': question, 'answer': answer, 'annotation': annotation_shuffled, 'images': images_shuffled}
    
    
    
    
    
    
