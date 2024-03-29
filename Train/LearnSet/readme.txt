Набор обучающих данных для дорожек: "Anaphora Resolution", "Coreference"
Обучающие корпуса для распознавания анафоры и для распознавания кореферентных цепочек.
Набор обучающих данных состоит из:
1. AnaphFiles.zip - архив с текстами без разметки. В корпус вошло 94 текста объемом не более 100 предложений (несоклько текстов больше).
2. anaph.xml - файл с разметкой анафорических отношений
3. coref.xml - файл с разметко кореферентных цепочек

Формат данных coref.xml:
<documents>
  <document id="2" file="OFC/2.txt" url="">
    <title><![CDATA[«Школа злословия» учит прикусить язык Сохранится ли градус дискуссии в новом сезоне?]]></title>
    <chain>
      <item sh="13" ln="17" ref="def" str="noun" type="coref">
        <cont><![CDATA[«Школа злословия»]]></cont>
      </item>
      <item sh="96" ln="9" ref="def" str="noun" type="coref">
        <cont><![CDATA[программы]]></cont>
      </item>
	  ...
    </chain>
    ...    
	</document>
	
id="2" - номер файла на сайте ant.compling.net 
file="OFC/2.txt" - имя и адрес файла в папках AnaphFiles.zip
    <title><![CDATA[«Школа злословия» учит прикусить язык Сохранится ли градус дискуссии в новом сезоне?]]></title> - заголовок
	<chain> - начало кореферентной цепочки.
	Цепочка состоит из групп, связанных между собой кореферентной или некоторыми другими типами связей (квазикореферентными)
	<item sh="13" ln="17" ref="def" str="noun" type="coref"> - 
sh - смещение группы (референциального выражения) от начала текста в символах, 
ln - длина группы в символах
Далее мы оставили атрибуты групп, которые мы использовали при разметке:
ref - тип отношения между группами в цепочке (см. ниже);
str - тип именной группы (см. ниже)
type - относится ли цепочка к кореферентной дорожке (Coreference) или только к дорожке по анафоре (см. регламент)

В файле с разметкой	 по анафоре в chain может входить только 2 именных группы (item): местоименная именная группа и ее антецедент. Если в цепочке более одного местоимения, то в паре в качестве антецедента указывается местоимение. Всю цепочку можно установить по свопадению смещений в разных цепочках.
	
Для того, чтобы воспользоваться разметкой следует иметь в виду следующие правила разметки данных:
1) в цепочке по кореферентности мы старались, по-возможности, размечать только конкретные объекты (но в текстах встречалось очень много сложных случаев, про которые не всегда поянтно. Например, альбом певцов правительство госыдартсва и название госыдарства и т.п., также встречались нереферентные цепочки (абстрактные объекты), для которых можно было проследить кореферентную цепочку однозначно. В данном случае иногда мы оставляли разметку).
2) в цепочках по анафоре рассматривались местоимения: он (она, оно, они), себя, тот (в анафорческом употреблении), который, свой, его, ее, их, этот: но: не рассматривалась анафора к событиям, к целым предикациям и к прямой речи;

Условные обозначения для атрибутов групп (item):
ref - тип отношения:
def - по умолчанию, кореферентность между двумя конкретно референтными группами
pred - группа имеет предикативный статус, т.е. не называет конкертный объект, а задает его класс: например, Его называют "Большим боссом" - большой босс имеет предикативный статус. Он может быть и не размечен системой, за это не следует штраф. Если система размечает такой случай, она также не штрафуется
		!!!NB - к сожалению, такой тип связи размечался непоследовательно
		факультативная связь в цепочке не оценивается
misc - факультативная связь в цепочке, не оценивается, 2 группы находятся в некотором отношении, но разметчик не уверен, что это отношение подлежит разметки, одна из ИГ либо обозначает не вполне тождественный объект, либо не конкретный объект
ds - ссылка на колркетный объект в прямой речи (метосимения 1 и 2 лица), 
		!!! NB факультативная связь в цепочке, не оценивается, размечалось непоследовательно

		
NB если ваша система связывает какую-то группу с одной из перечисленных выше факультативных, мы считаем это допустимым решением

str - тип именной группы:
noun - группа состоит из полнозначных слов (содержит существительные)
pron - группа состоит из местоимений он (она, оно, они), тот
refl - группа состоит из местоимений себя, свой
rel - группа состоит из местоимения который
dem - в группу входит метосимение этот (размечено не до конца последовательно)

type
coref - если группа относится к кореферентной цепочке. Эта же группа может относиться к анафорической паре, если она представляет собой местоимение из списка.
anaph - если группа обозначает некоторый абстрактный объект и не попадает поэтому в разметку кореферентных цепочек, попадает только в разметку анафоры.


NB На сайте можно увидеть еще размеченные потенциальные вершины групп - "допустимые". Если данная информация нужна, мы можем включить ее в обучающий корпус.

	


